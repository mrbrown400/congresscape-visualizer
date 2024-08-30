import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { UsersIcon } from 'lucide-react';
import HouseSeatingChart from '../components/HouseSeatingChart';

const CongressVisualization = () => {
  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-bold">Current US House of Representatives Seating Chart</h1>
        <Link to="/senate">
          <Button variant="outline">
            <UsersIcon className="mr-2 h-4 w-4" />
            View Senate
          </Button>
        </Link>
      </div>
      <HouseSeatingChart />
      <p className="mt-4 text-sm text-gray-600">
        Note: This visualization shows the current seating arrangement in the US House of Representatives.
        Each dot represents a member, colored according to their party affiliation (Blue for Democrats, Red for Republicans, Gray for others).
      </p>
    </div>
  );
};

export default CongressVisualization;
