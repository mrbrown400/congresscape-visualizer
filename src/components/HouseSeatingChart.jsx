import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"

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

  const members = data?.members || [];

  return (
    <div className="grid grid-cols-25 gap-1 p-4 bg-gray-100 rounded-lg">
      {members.map((member, index) => (
        <div
          key={member.id || index}
          className={`w-4 h-4 rounded-full ${
            member.party === 'D' ? 'bg-blue-500' :
            member.party === 'R' ? 'bg-red-500' :
            'bg-gray-500'
          }`}
          title={`${member.name} (${member.party})`}
        />
      ))}
    </div>
  );
};

export default HouseSeatingChart;
