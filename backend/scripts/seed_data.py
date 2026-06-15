import asyncio
import sys
import os
import random
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.session import get_session
from app.schemas.update import GovernmentUpdateCreate
from app.services.update_service import UpdateService
from app.models.update import BranchEnum

BRANCHES = [BranchEnum.LEGISLATIVE, BranchEnum.EXECUTIVE, BranchEnum.JUDICIAL]
SOURCES = {
    BranchEnum.LEGISLATIVE: "congress.gov",
    BranchEnum.EXECUTIVE: "whitehouse.gov",
    BranchEnum.JUDICIAL: "supremecourt.gov"
}

TITLES = {
    BranchEnum.LEGISLATIVE: [
        "H.R. {num} - To improve federal infrastructure",
        "S. {num} - A bill to regulate AI safety",
        "H.Res. {num} - Congratulating the National Champions",
        "S.J.Res. {num} - Disapproving the rule submitted by the EPA",
        "H.R. {num} - The Clean Energy Act of 2025"
    ],
    BranchEnum.EXECUTIVE: [
        "Executive Order on Safe, Secure, and Trustworthy Artificial Intelligence",
        "Proclamation on National Cybersecurity Awareness Month",
        "Memorandum on Restoring Trust in Government Science",
        "Remarks by President Biden on the Economy",
        "Statement from the Press Secretary on Foreign Aid"
    ],
    BranchEnum.JUDICIAL: [
        "Opinion of the Court in Smith v. United States",
        "Order in Pending Case 24-{num}",
        "Certiorari Granted in Doe v. Agency",
        "Argument Transcript: City of Austin v. Reagan",
        "Dissenting Opinion in State v. Federal Bureau"
    ]
}

async def seed_data():
    print("Seeding database with mock data...")
    async for session in get_session():
        service = UpdateService(session)
        
        # Generate data for the current year and previous year
        start_date = datetime.now(timezone.utc).replace(year=2024, month=1, day=1)
        end_date = datetime.now(timezone.utc)
        
        current = start_date
        count = 0
        
        while current <= end_date:
            # Randomly decide if there's activity today (70% chance)
            if random.random() < 0.7:
                # Generate 1-3 updates for this day
                num_updates = random.randint(1, 3)
                for _ in range(num_updates):
                    branch = random.choice(BRANCHES)
                    template = random.choice(TITLES[branch])
                    title = template.format(num=random.randint(100, 9999))
                    
                    payload = GovernmentUpdateCreate(
                        external_id=f"seed-{count}",
                        source=SOURCES[branch],
                        branch=branch,
                        headline=title,
                        summary=f"This is a generated summary for {title}. It contains mock data for demonstration purposes.",
                        full_text=f"Full text content for {title}...",
                        published_at=current + timedelta(hours=random.randint(8, 18)),
                        url="https://example.com",
                        tags=["demo", "seed", branch.value],
                        metadata={"seeded": True}
                    )
                    await service.upsert_update(payload)
                    count += 1
            
            current += timedelta(days=1)
        
        await session.commit()
        print(f"Seeding complete! Added {count} updates.")
        break

if __name__ == "__main__":
    asyncio.run(seed_data())
