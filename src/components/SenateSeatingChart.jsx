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
    ...member,
    party: member.partyName || 
           (member.parties && member.parties[0] && member.parties[0].name) || 
           'Unknown'
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

  const members = Array.isArray(data) ? data : [];

  return (
    <TooltipProvider>
      <div className="grid grid-cols-10 gap-2 p-4 bg-gray-100 rounded-lg">
        {members.slice(0, 100).map((member, index) => (
          <Tooltip key={member.bioguideId || index}>
            <TooltipTrigger>
              <div
                className={`w-8 h-8 rounded-full ${getPartyColor(member.party)}`}
              />
            </TooltipTrigger>
            <TooltipContent>
              <p>{member.name} ({member.party})</p>
              <p>{member.state}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
};

export default SenateSeatingChart;