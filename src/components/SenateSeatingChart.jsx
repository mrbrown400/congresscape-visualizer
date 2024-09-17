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
  const { data: senators, isLoading, error } = useQuery({
    queryKey: ['senateMembers'],
    queryFn: fetchSenateMembers,
  });

  if (isLoading) {
    return <Skeleton className="w-full h-[400px] rounded-lg" />;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error.message}</AlertDescription>
      </Alert>
    );
  }

  const isEvenlySplit = senators.filter(m => m.party === 'Democratic').length === senators.filter(m => m.party === 'Republican').length;

  // Create a semi-circular layout
  const rows = 5;
  const seatsPerRow = Math.ceil(senators.length / rows);
  const seatingArrangement = Array.from({ length: rows }, (_, rowIndex) =>
    senators.slice(rowIndex * seatsPerRow, (rowIndex + 1) * seatsPerRow)
  );

  return (
    <TooltipProvider>
      <div className="relative w-full h-[400px] bg-gray-100 rounded-lg overflow-hidden">
        {isEvenlySplit && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2">
            <Tooltip>
              <TooltipTrigger>
                <div className="w-8 h-8 rounded-full bg-blue-500 border-4 border-yellow-400" />
              </TooltipTrigger>
              <TooltipContent>
                <p>Vice President (Tie-breaking vote)</p>
              </TooltipContent>
            </Tooltip>
          </div>
        )}
        <div className="absolute bottom-0 left-0 right-0 h-5/6">
          {seatingArrangement.map((row, rowIndex) => (
            <div
              key={rowIndex}
              className="absolute left-1/2 bottom-0 transform -translate-x-1/2"
              style={{
                height: `${100 - (rowIndex * 15)}%`,
                width: `${100 - (rowIndex * 10)}%`,
              }}
            >
              {row.map((senator, seatIndex) => (
                <Tooltip key={`${rowIndex}-${seatIndex}`}>
                  <TooltipTrigger>
                    <div
                      className={`absolute w-4 h-4 rounded-full ${getPartyColor(senator.party)} ${senator.isLeader ? 'border-2 border-purple-500' : ''}`}
                      style={{
                        left: `${(seatIndex / (row.length - 1)) * 100}%`,
                        bottom: '0',
                        transform: 'translate(-50%, 50%)',
                      }}
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
      </div>
    </TooltipProvider>
  );
};

export default SenateSeatingChart;
