import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { HomeIcon } from 'lucide-react';
import SenateSeatingChart from '../components/SenateSeatingChart';

const SenateVisualization = () => {
  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-bold">Current US Senate Seating Chart</h1>
        <Link to="/house">
          <Button variant="outline">
            <HomeIcon className="mr-2 h-4 w-4" />
            View House
          </Button>
        </Link>
      </div>
      <SenateSeatingChart />
      <p className="mt-4 text-sm text-gray-600">
        Note: This visualization shows the current seating arrangement in the US Senate.
        Each dot represents a senator, colored according to their party affiliation (Blue for Democrats, Red for Republicans, Gray for others).
      </p>
    </div>
  );
};

export default SenateVisualization;
