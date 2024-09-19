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
      <div className="flex justify-center items-center h-96">
        <Skeleton className="w-full h-full rounded-lg" />
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
    if (a.party !== b.party) return a.party.localeCompare(b.party);
    return a.state.localeCompare(b.state);
  });

  const isEvenlySplit = senators.filter(m => m.party === 'Democratic').length === senators.filter(m => m.party === 'Republican').length;

  return (
    <TooltipProvider>
      <div className="flex flex-col items-center">
        {isEvenlySplit && (
          <div className="mb-4">
            <Tooltip>
              <TooltipTrigger>
                <div className="w-12 h-12 rounded-full bg-blue-500 border-4 border-yellow-400" />
              </TooltipTrigger>
              <TooltipContent>
                <p>Vice President (Tie-breaking vote)</p>
              </TooltipContent>
            </Tooltip>
          </div>
        )}
        <div className="relative w-[600px] h-[300px] bg-gray-100 rounded-[50%] overflow-hidden">
          {sortedSenators.map((senator, index) => {
            const angle = (index / senators.length) * Math.PI;
            const x = 300 + Math.cos(angle) * (250 - Math.random() * 30);
            const y = 150 + Math.sin(angle) * (125 - Math.random() * 15);
            return (
              <Tooltip key={index}>
                <TooltipTrigger>
                  <div
                    className={`absolute w-6 h-6 rounded-full ${getPartyColor(senator.party)} ${senator.isLeader ? 'border-2 border-purple-500' : ''}`}
                    style={{ left: `${x}px`, top: `${y}px` }}
                  />
                </TooltipTrigger>
                <TooltipContent>
                  <p>{senator.name}</p>
                  <p>{getPartyAbbreviation(senator.party)} - {senator.state}</p>
                  {senator.isLeader && <p>Leadership: {senator.leadership}</p>}
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      </div>
    </TooltipProvider>
  );
};

export default SenateSeatingChart;
