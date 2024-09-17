import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

const fetchHouseMembers = async () => {
  const apiKey = import.meta.env.VITE_CONGRESS_API_KEY;
  if (!apiKey) {
    throw new Error('Congress API key not found. Please add it to your .env file.');
  }
  const response = await fetch(`https://api.congress.gov/v3/member?chamber=house&api_key=${apiKey}&limit=450`);
  if (!response.ok) {
    throw new Error('Failed to fetch House members');
  }
  const data = await response.json();
  return data.members.map(member => ({
    name: `${member.firstName} ${member.lastName}`,
    party: member.partyName || 'Unknown',
    state: member.state,
    district: member.district,
    leadership: member.leadership || [],
    isLeader: member.leadership && member.leadership.length > 0,
    isSpeaker: member.leadership && member.leadership.some(role => role.toLowerCase().includes('speaker'))
  }));
};

const getPartyColor = (party) => {
  switch (party) {
    case 'Democratic':
    case 'D':
      return 'bg-blue-500';
    case 'Republican':
    case 'R':
      return 'bg-red-500';
    case 'Independent':
    case 'I':
      return 'bg-yellow-500';
    default:
      return 'bg-gray-500';
  }
};

const HouseSeatingChart = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['houseMembers'],
    queryFn: fetchHouseMembers,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[600px] bg-gray-100 rounded-lg">
        <Skeleton className="w-full h-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    );
  }

  const members = Array.isArray(data) ? data : [];
  const speaker = members.find(member => member.isSpeaker);

  const createCurvedLayout = (members, rows, seatsPerRow) => {
    const layout = [];
    let memberIndex = 0;

    for (let row = 0; row < rows; row++) {
      const rowSeats = [];
      const actualSeatsInRow = Math.min(seatsPerRow, members.length - memberIndex);
      
      for (let seat = 0; seat < actualSeatsInRow; seat++) {
        if (memberIndex < members.length) {
          rowSeats.push(members[memberIndex]);
          memberIndex++;
        }
      }
      layout.push(rowSeats);
    }

    return layout;
  };

  const curvedLayout = createCurvedLayout(members.filter(m => !m.isSpeaker), 9, 50);

  return (
    <TooltipProvider>
      <div className="flex flex-col items-center justify-center bg-gray-100 rounded-lg p-8">
        <div className="mb-8">
          {speaker && (
            <Tooltip>
              <TooltipTrigger>
                <div className={`w-8 h-8 rounded-full ${getPartyColor(speaker.party)} border-4 border-green-400`} />
              </TooltipTrigger>
              <TooltipContent>
                <p>{speaker.name} ({speaker.party})</p>
                <p>{speaker.state} - District {speaker.district}</p>
                <p>Speaker of the House</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
        {curvedLayout.map((row, rowIndex) => (
          <div
            key={rowIndex}
            className="flex justify-center"
            style={{
              transform: `rotate(${(rowIndex - 4) * 3}deg)`,
              marginBottom: `-${rowIndex * 2}px`,
            }}
          >
            {row.map((member, seatIndex) => (
              <Tooltip key={`${rowIndex}-${seatIndex}`}>
                <TooltipTrigger>
                  <div
                    className={`w-3 h-3 rounded-full ${getPartyColor(member.party)} ${
                      member.isLeader ? 'border border-purple-500' : ''
                    } mx-0.5`}
                  />
                </TooltipTrigger>
                <TooltipContent>
                  <p>{member.name} ({member.party})</p>
                  <p>{member.state} - District {member.district}</p>
                  {member.isLeader && <p>Leadership: {member.leadership.join(', ')}</p>}
                </TooltipContent>
              </Tooltip>
            ))}
          </div>
        ))}
      </div>
    </TooltipProvider>
  );
};

export default HouseSeatingChart;
