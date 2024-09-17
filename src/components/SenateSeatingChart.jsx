import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

const fetchSenateMembers = async () => {
  const apiKey = import.meta.env.VITE_CONGRESS_API_KEY;
  if (!apiKey) {
    throw new Error('Congress API key not found. Please add it to your .env file.');
  }
  const response = await fetch(`https://api.congress.gov/v3/member?chamber=senate&api_key=${apiKey}&limit=100`);
  if (!response.ok) {
    throw new Error('Failed to fetch Senate members');
  }
  const data = await response.json();
  
  return data.members.map(member => ({
    name: `${member.firstName} ${member.lastName}`,
    party: member.partyName || 'Unknown',
    state: member.state,
    leadership: member.leadership || [],
    isLeader: member.leadership && member.leadership.length > 0
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

const SenateSeatingChart = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['senateMembers'],
    queryFn: fetchSenateMembers,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-[400px] bg-gray-100 rounded-lg">
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

  if (!data) {
    return (
      <Alert>
        <AlertTitle>No Data</AlertTitle>
        <AlertDescription>No senate data available.</AlertDescription>
      </Alert>
    );
  }

  const senators = data;
  const isEvenlySplit = senators.filter(m => m.party === 'Democratic').length === senators.filter(m => m.party === 'Republican').length;

  const createSemiCircleLayout = (senators) => {
    const layout = [];
    const rows = 5;
    const seatsPerRow = Math.ceil(senators.length / rows);

    for (let row = 0; row < rows; row++) {
      const rowSeats = senators.slice(row * seatsPerRow, (row + 1) * seatsPerRow);
      layout.push(rowSeats);
    }

    return layout;
  };

  const semiCircleLayout = createSemiCircleLayout(senators);

  return (
    <TooltipProvider>
      <div className="flex flex-col items-center justify-center bg-gray-100 rounded-lg p-8">
        <div className="mb-8">
          {isEvenlySplit && (
            <Tooltip>
              <TooltipTrigger>
                <div className="w-8 h-8 rounded-full bg-blue-500 border-4 border-yellow-400" />
              </TooltipTrigger>
              <TooltipContent>
                <p>Vice President (Tie-breaking vote)</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
        {semiCircleLayout.map((row, rowIndex) => (
          <div
            key={rowIndex}
            className="flex justify-center"
            style={{
              transform: `rotate(${(rowIndex - 2) * 5}deg)`,
              marginBottom: `-${rowIndex * 4}px`,
            }}
          >
            {row.map((senator, seatIndex) => (
              <Tooltip key={`${rowIndex}-${seatIndex}`}>
                <TooltipTrigger>
                  <div
                    className={`w-4 h-4 rounded-full ${getPartyColor(senator.party)} ${
                      senator.isLeader ? 'border-2 border-purple-500' : ''
                    } mx-1`}
                  />
                </TooltipTrigger>
                <TooltipContent>
                  <p>{senator.name} ({senator.party})</p>
                  <p>{senator.state}</p>
                  {senator.isLeader && <p>Leadership: {senator.leadership.join(', ')}</p>}
                </TooltipContent>
              </Tooltip>
            ))}
          </div>
        ))}
      </div>
    </TooltipProvider>
  );
};

export default SenateSeatingChart;
