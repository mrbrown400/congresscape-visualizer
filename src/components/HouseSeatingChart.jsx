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
    ...member,
    party: member.partyName || 
           (member.parties && member.parties[0] && member.parties[0].name) || 
           'Unknown',
    isLeader: member.leadership && member.leadership.some(role => 
      role.toLowerCase().includes('majority leader') || 
      role.toLowerCase().includes('minority leader')
    ),
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

  const members = Array.isArray(data) ? data : [];
  const speaker = members.find(member => member.isSpeaker);

  return (
    <TooltipProvider>
      <div className="grid grid-cols-25 gap-1 p-4 bg-gray-100 rounded-lg">
        {speaker && (
          <div className="col-span-25 flex justify-center mb-4">
            <Tooltip>
              <TooltipTrigger>
                <div className={`w-8 h-8 rounded-full ${getPartyColor(speaker.party)} border-4 border-green-400`} />
              </TooltipTrigger>
              <TooltipContent>
                <p>{speaker.name} ({speaker.party})</p>
                <p>{speaker.state}</p>
                <p>Speaker of the House</p>
              </TooltipContent>
            </Tooltip>
          </div>
        )}
        {members.filter(m => !m.isSpeaker).map((member, index) => (
          <Tooltip key={member.bioguideId || index}>
            <TooltipTrigger>
              <div
                className={`w-4 h-4 rounded-full ${getPartyColor(member.party)} ${member.isLeader ? 'border-2 border-purple-500' : ''}`}
              />
            </TooltipTrigger>
            <TooltipContent>
              <p>{member.name} ({member.party})</p>
              <p>{member.state}</p>
              {member.isLeader && <p>Party Leader</p>}
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
};

export default HouseSeatingChart;
