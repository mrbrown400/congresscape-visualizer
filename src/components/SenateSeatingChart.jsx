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
    name: `${member.name || ''} `,
    party: member.partyName || 'Unknown',
    state: member.state,
    leadership: member.leadershipRole || [],
    isLeader: member.leadershipRole ? true : false
  }));
};

const getPartyColor = (party) => {
  switch (party) {
    case 'Democratic':
      return 'bg-blue-500';
    case 'Republican':
      return 'bg-red-500';
    case 'Independent':
      return 'bg-yellow-500';
    default:
      return 'bg-gray-500';
  }
};

const getPartyAbbreviation = (party) => {
  switch (party) {
    case 'Democratic':
      return 'D';
    case 'Republican':
      return 'R';
    case 'Independent':
      return 'I';
    default:
      return 'U';
  }
};

const SenateSeatingChart = () => {
  const { data: senators, isLoading, error } = useQuery({
    queryKey: ['senateMembers'],
    queryFn: fetchSenateMembers,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-5 gap-1 p-4 bg-gray-100 rounded-lg">
        {[...Array(100)].map((_, index) => (
          <Skeleton key={index} className="w-8 h-8 rounded-full" />
        ))}
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

  const sortedSenators = senators.sort((a, b) => {
    if (a.party === b.party) {
      return a.state.localeCompare(b.state);
    }
    return a.party === 'Republican' ? -1 : 1;
  });

  const seatsPerColumn = Math.ceil(sortedSenators.length / 5);

  return (
    <TooltipProvider>
      <div className="flex flex-col items-center">
        <div className="grid grid-flow-col auto-cols-fr gap-1">
          {[...Array(5)].map((_, colIndex) => (
            <div key={colIndex} className="flex flex-col gap-1">
              {sortedSenators.slice(colIndex * seatsPerColumn, (colIndex + 1) * seatsPerColumn).map((senator, index) => (
                <Tooltip key={index}>
                  <TooltipTrigger>
                    <div
                      className={`w-8 h-8 rounded-full ${getPartyColor(senator.party)} ${senator.isLeader ? 'border-4 border-purple-500' : ''}`}
                    />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{senator.name}</p>
                    <p>{getPartyAbbreviation(senator.party)} - {senator.state}</p>
                    {senator.isLeader && <p>Leadership: {senator.leadership}</p>}
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
