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
      <div className="grid grid-cols-11 gap-1 p-4 bg-gray-100 rounded-lg">
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
  const sortedMembers = members.sort((a, b) => {
    if (a.party === b.party) {
      if (a.state === b.state) {
        const districtA = String(a.district || '');
        const districtB = String(b.district || '');
        return districtA.localeCompare(districtB);
      }
      return a.state.localeCompare(b.state);
    }
    return a.party === 'Republican' ? -1 : 1;
  }).filter(member => !member.isSpeaker);

  const seatsPerColumn = Math.ceil(sortedMembers.length / 11);

  return (
    <TooltipProvider>
      <div className="flex flex-col items-center">
        <div className="mb-4">
          {speaker && (
            <Tooltip>
              <TooltipTrigger>
                <div className={`w-6 h-6 rounded-full ${getPartyColor(speaker.party)} border-4 border-green-400`} />
              </TooltipTrigger>
              <TooltipContent>
                <p>{speaker.name}</p>
                <p>{getPartyAbbreviation(speaker.party)} - {speaker.state}, District {speaker.district || 'At-Large'}</p>
                <p>Speaker of the House</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
        <div className="grid grid-flow-col auto-cols-fr gap-1">
          {[...Array(11)].map((_, colIndex) => (
            <div key={colIndex} className="flex flex-col gap-1">
              {sortedMembers.slice(colIndex * seatsPerColumn, (colIndex + 1) * seatsPerColumn).map((member, index) => (
                <Tooltip key={index}>
                  <TooltipTrigger>
                    <div
                      className={`w-6 h-6 rounded-full ${getPartyColor(member.party)} ${member.isLeader ? 'border-2 border-purple-500' : ''}`}
                    />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{member.name}</p>
                    <p>{getPartyAbbreviation(member.party)} - {member.state}, District {member.district || 'At-Large'}</p>
                    {member.isLeader && <p>Leadership: {member.leadership}</p>}
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

export default HouseSeatingChart;
