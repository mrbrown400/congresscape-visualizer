import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { HomeIcon, UsersIcon } from 'lucide-react';

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100">
      <h1 className="text-4xl font-bold mb-8">CongressScape Visualizer</h1>
      <div className="space-y-4">
        <Link to="/house">
          <Button className="w-64 text-lg" variant="default">
            <HomeIcon className="mr-2 h-5 w-5" />
            House Visualization
          </Button>
        </Link>
        <Link to="/senate">
          <Button className="w-64 text-lg" variant="default">
            <UsersIcon className="mr-2 h-5 w-5" />
            Senate Visualization
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default Index;