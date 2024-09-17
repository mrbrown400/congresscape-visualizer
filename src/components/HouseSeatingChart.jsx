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
    return <Skeleton className="w-full h-[600px] rounded-lg" />;
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
  const otherMembers = members.filter(member => !member.isSpeaker);

  // Create a curved layout
  const rows = 9;
  const seatsPerRow = Math.ceil(otherMembers.length / rows);
  const seatingArrangement = Array.from({ length: rows }, (_, rowIndex) =>
    otherMembers.slice(rowIndex * seatsPerRow, (rowIndex + 1) * seatsPerRow)
  );

  return (
    <TooltipProvider>
      <div className="relative w-full h-[600px] bg-gray-100 rounded-lg overflow-hidden">
        {speaker && (
          <div className="absolute top-4 left-1/2 transform -translate-x-1/2">
            <Tooltip>
              <TooltipTrigger>
                <div className={`w-8 h-8 rounded-full ${getPartyColor(speaker.party)} border-4 border-green-400`} />
              </TooltipTrigger>
              <TooltipContent>
                <p>{speaker.name} ({speaker.party})</p>
                <p>{speaker.state} - District {speaker.district}</p>
                <p>Speaker of the House</p>
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
                height: `${100 - (rowIndex * 10)}%`,
                width: `${100 - (rowIndex * 5)}%`,
              }}
            >
              {row.map((member, seatIndex) => (
                <Tooltip key={`${rowIndex}-${seatIndex}`}>
                  <TooltipTrigger>
                    <div
                      className={`absolute w-3 h-3 rounded-full ${getPartyColor(member.party)} ${member.isLeader ? 'border-2 border-purple-500' : ''}`}
                      style={{
                        left: `${(seatIndex / (row.length - 1)) * 100}%`,
                        bottom: '0',
                        transform: 'translate(-50%, 50%)',
                      }}
                    />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{member.name} ({member.party})</p>
                    <p>{member.state} - District {member.district}</p>
                    {member.isLeader && <p>Leadership: {member.leadership.join(', ')}</p>}
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
