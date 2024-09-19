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
    name: `${member.name || ''}`,
    party: member.partyName || 'Unknown',
    state: member.state,
    district: member.district,
    leadership: member.leadershipRole || [],
    isLeader: member.leadershipRole ? true : false,
    isSpeaker: member.leadershipRole && member.leadershipRole.toLowerCase().includes('speaker')
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

const HouseSeatingChart = () => {
  const { data: members, isLoading, error } = useQuery({
    queryKey: ['houseMembers'],
    queryFn: fetchHouseMembers,
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

  const speaker = members.find(member => member.isSpeaker);
  const sortedMembers = members.sort((a, b) => {
    if (a.party !== b.party) return a.party.localeCompare(b.party);
    if (a.state !== b.state) return a.state.localeCompare(b.state);
    // Convert district to string and use localeCompare, or fallback to 0 if district is undefined
    return (a.district?.toString() || '').localeCompare(b.district?.toString() || '');
  });

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
                <p>{getPartyAbbreviation(speaker.party)} - {speaker.state}, District {speaker.district}</p>
                <p>Speaker of the House</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
        <div className="relative w-[800px] h-[400px] bg-gray-100 rounded-[50%] overflow-hidden">
          {sortedMembers.filter(m => !m.isSpeaker).map((member, index) => {
            const angle = (index / (sortedMembers.length - 1)) * Math.PI;
            const x = 400 + Math.cos(angle) * (350 - Math.random() * 50);
            const y = 200 + Math.sin(angle) * (175 - Math.random() * 25);
            return (
              <Tooltip key={index}>
                <TooltipTrigger>
                  <div
                    className={`absolute w-4 h-4 rounded-full ${getPartyColor(member.party)} ${member.isLeader ? 'border-2 border-purple-500' : ''}`}
                    style={{ left: `${x}px`, top: `${y}px` }}
                  />
                </TooltipTrigger>
                <TooltipContent>
                  <p>{member.name}</p>
                  <p>{getPartyAbbreviation(member.party)} - {member.state}, District {member.district || 'At-Large'}</p>
                  {member.isLeader && <p>Leadership: {member.leadership}</p>}
                </TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      </div>
    </TooltipProvider>
  );
};

export default HouseSeatingChart;
