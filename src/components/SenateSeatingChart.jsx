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
      <div className="grid grid-cols-10 gap-2 p-4 bg-gray-100 rounded-lg">
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

  return (
    <TooltipProvider>
      <div className="grid grid-cols-10 gap-2 p-4 bg-gray-100 rounded-lg">
        {isEvenlySplit && (
          <div className="col-span-10 flex justify-center mb-4">
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
        {senators.map((senator, index) => (
          <Tooltip key={index}>
            <TooltipTrigger>
              <div
                className={`w-8 h-8 rounded-full ${getPartyColor(senator.party)} ${senator.isLeader ? 'border-4 border-purple-500' : ''}`}
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
    </TooltipProvider>
  );
};

export default SenateSeatingChart;