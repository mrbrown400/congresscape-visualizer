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
  const { data: members, isLoading, error } = useQuery({
    queryKey: ['houseMembers'],
    queryFn: fetchHouseMembers,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-25 gap-1 p-4 bg-gray-100 rounded-lg">
        {[...Array(435)].map((_, index) => (
          <Skeleton key={index} className="w-4 h-4 rounded-full" />
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

  const speaker = members.find(member => member.isSpeaker);

  return (
    <TooltipProvider>
      <div className="flex flex-col items-center">
        <div className="mb-4">
          {speaker && (
            <Tooltip>
              <TooltipTrigger>
                <div className={`w-8 h-8 rounded-full ${getPartyColor(speaker.party)} border-4 border-green-400`} />
              </TooltipTrigger>
              <TooltipContent>
                <p>{speaker.name}</p>
                <p>{speaker.party} - {speaker.state}, District {speaker.district}</p>
                <p>Speaker of the House</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
        <div className="flex flex-wrap justify-center max-w-4xl">
          {members.filter(m => !m.isSpeaker).map((member, index) => (
            <Tooltip key={index}>
              <TooltipTrigger>
                <div
                  className={`w-4 h-4 m-1 rounded-full ${getPartyColor(member.party)} ${member.isLeader ? 'border-2 border-purple-500' : ''}`}
                />
              </TooltipTrigger>
              <TooltipContent>
                <p>{member.name}</p>
                <p>{member.party} - {member.state}, District {member.district}</p>
                {member.isLeader && <p>Leadership: {member.leadership.join(', ')}</p>}
              </TooltipContent>
            </Tooltip>
          ))}
        </div>
      </div>
    </TooltipProvider>
  );
};

export default HouseSeatingChart;
