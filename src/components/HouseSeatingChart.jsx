import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

const fetchHouseMembers = async () => {
  const apiKey = import.meta.env.VITE_CONGRESS_API_KEY;
  if (!apiKey) {
    throw new Error('Congress API key not found. Please add it to your .env file.');
  }
  const response = await fetch(`https://api.congress.gov/v3/member?chamber=house&api_key=${apiKey}`);
  if (!response.ok) {
    throw new Error('Failed to fetch House members');
  }
  return response.json();
};

const HouseSeatingChart = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['houseMembers'],
    queryFn: fetchHouseMembers,
  });

  if (isLoading) {
    return (
      <div className="flex flex-wrap justify-center items-center gap-1 p-4 bg-gray-100 rounded-lg" style={{ maxWidth: '800px', margin: '0 auto' }}>
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

  const members = data?.members || [];

  // Function to determine the position of each seat
  const getPosition = (index) => {
    const row = Math.floor(index / 25);
    const col = index % 25;
    const angle = (col - 12) * 3; // Adjust for curvature
    const radius = 400 - row * 30; // Adjust for multiple rows
    const x = radius * Math.sin(angle * Math.PI / 180);
    const y = radius * Math.cos(angle * Math.PI / 180);
    return { transform: `translate(${x}px, ${y}px)` };
  };

  return (
    <TooltipProvider>
      <div className="relative w-[800px] h-[400px] mx-auto bg-gray-100 rounded-lg overflow-hidden">
        {members.map((member, index) => (
          <Tooltip key={member.id || index}>
            <TooltipTrigger>
              <div
                className={`absolute w-4 h-4 rounded-full ${
                  member.party === 'D' ? 'bg-blue-500' :
                  member.party === 'R' ? 'bg-red-500' :
                  'bg-gray-500'
                } hover:ring-2 hover:ring-white transition-all duration-200`}
                style={getPosition(index)}
              />
            </TooltipTrigger>
            <TooltipContent>
              <p>{member.name} ({member.party})</p>
              <p className="text-xs">{member.state}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
};

export default HouseSeatingChart;
