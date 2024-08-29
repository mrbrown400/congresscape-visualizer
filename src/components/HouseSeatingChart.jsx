import React from 'react';
import { useQuery } from '@tanstack/react-query';

const fetchHouseMembers = async () => {
  const response = await fetch('https://api.congress.gov/v3/member?chamber=house&api_key=YOUR_API_KEY_HERE');
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

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  const members = data.members || [];

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