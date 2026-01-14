import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import LoadingSkeleton from "./LoadingSkeleton";

export default function LoadingDemo() {
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("card");

  const toggleLoading = () => {
    setIsLoading(!isLoading);
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Loading Skeleton Demo</h1>
          <p className="text-muted-foreground">
            A collection of professional loading skeletons for different UI
            patterns
          </p>
        </div>
        <Button onClick={toggleLoading} variant="outline">
          {isLoading ? "Show Content" : "Show Loading"}
        </Button>
      </div>

      <Tabs defaultValue="card" value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-5 w-full max-w-2xl">
          <TabsTrigger value="card">Cards</TabsTrigger>
          <TabsTrigger value="list">List</TabsTrigger>
          <TabsTrigger value="table">Table</TabsTrigger>
          <TabsTrigger value="detail">Detail</TabsTrigger>
          <TabsTrigger value="full">Full Page</TabsTrigger>
        </TabsList>

        <div className="mt-6">
          {isLoading ? (
            <LoadingSkeleton
              type={activeTab as "card" | "list" | "table" | "detail" | "full"}
              count={activeTab === "list" ? 5 : 3}
              text={`Loading ${activeTab} data...`}
            />
          ) : (
            <div className="p-12 border border-border rounded-lg flex items-center justify-center">
              <p className="text-muted-foreground">Content would appear here</p>
            </div>
          )}
        </div>
      </Tabs>
    </div>
  );
}
