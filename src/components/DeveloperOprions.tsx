import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useArchiveStore } from "@/hooks/store";
import { readConfig } from "@/lib/readConfig";
import { writeConfig } from "@/lib/writeConfig";
import { restart } from "@/lib/xmlrpc";
import { message } from "@tauri-apps/plugin-dialog";
import {
  AlertCircle,
  Info,
  RefreshCw,
  Server,
  Settings,
  Terminal,
} from "lucide-react";
import { useEffect, useState } from "react";

const DeveloperOptions = () => {
  const [open, setOpen] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [config, setConfig] = useState({
    HOST: "localhost",
    PORT: "8080",
  });
  useEffect(() => {
    const getURL = async () => {
      const config = await readConfig();
      setConfig(config);
    };
    getURL();
  }, []);
  const fetchArchives = useArchiveStore((state) => state.fetchArchives);

  const handleConfigChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setConfig((prev) => ({ ...prev, [name]: value }));
  };

  const handleSaveConfig = async () => {
    // Save configuration logic would go here
    await writeConfig(config);
    await message(`Server settings updated to ${config.HOST}:${config.PORT}`, {
      title: "Configuration saved",
      kind: "info",
      // description: `Server settings updated to ${config.host}:${config.port}`,
    });
  };

  const handleRestart = async () => {
    try {
      setIsRestarting(true);
      await restart(false);
      await fetchArchives();
      await message(" Server restarted successfully", {
        title: "Server restarted",
        // description: "The XMLRPC server has been restarted successfully",
      });
    } catch (error) {
      await message(" Restart failed", {
        title: "Restart failed",
        // description: "Failed to restart the XMLRPC server",
        // variant: "destructive",
      });
    } finally {
      setIsRestarting(false);
    }
  };

  // Mock system information - in a real app, this would come from your backend

  const systemInfo = {
    os: "Linux Ubuntu 22.04 LTS",
    architecture: "x64",
    nodeVersion: "v18.17.0",
    appVersion: "1.2.3",
    uptime: "3 days, 7 hours",
    memoryUsage: "1.2 GB / 8 GB",
  };

  return (
    <>
      <Button
        onClick={() => setOpen(true)}
        variant="outline"
        size="sm"
        className="flex items-center gap-2"
      >
        <Settings className="h-4 w-4" />
        Developer Options
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <Terminal className="h-5 w-5" />
              Developer Options
            </DialogTitle>
            <DialogDescription>
              Advanced configuration settings for development and debugging
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="server" className="mt-4">
            <TabsList className="grid grid-cols-3 mb-4">
              <TabsTrigger value="server">Server</TabsTrigger>
              {/* <TabsTrigger value="system">System Info</TabsTrigger>
              <TabsTrigger value="logs">Logs</TabsTrigger> */}
            </TabsList>

            <TabsContent value="server" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-md flex items-center gap-2">
                    <Server className="h-4 w-4" />
                    XMLRPC Server Configuration
                  </CardTitle>
                  <CardDescription>
                    Configure connection settings for the XMLRPC server
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="HOST">Host</Label>
                      <Input
                        id="HOST"
                        name="HOST"
                        value={config.HOST}
                        onChange={handleConfigChange}
                        placeholder={config.HOST}
                        onFocus={(e) => e.target.select()}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="PORT">Port</Label>
                      <Input
                        id="PORT"
                        name="PORT"
                        value={config.PORT}
                        onChange={handleConfigChange}
                        placeholder={config.PORT}
                        onFocus={(e) => e.target.select()}
                      />
                    </div>
                  </div>
                  {/* <code className="">C:\Users\&lt;you&gt;\AppData\Local\Diabots.ArchivesManager\Diabots\config.json</code> */}
                  <div className="flex justify-between items-center pt-2">
                    <Button onClick={handleSaveConfig} variant="default">
                      Save Configuration
                    </Button>
                    <Button
                      onClick={handleRestart}
                      variant="outline"
                      className="flex items-center gap-2"
                      disabled={isRestarting}
                    >
                      {isRestarting ? (
                        <RefreshCw className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      Restart Server
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="system" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-md flex items-center gap-2">
                    <Info className="h-4 w-4" />
                    System Information
                  </CardTitle>
                  <CardDescription>
                    Details about the current environment and application
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        Operating System
                      </span>
                      <Badge variant="outline" className="font-mono">
                        {systemInfo.os}
                      </Badge>
                    </div>
                    <Separator />

                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Architecture</span>
                      <Badge variant="outline" className="font-mono">
                        {systemInfo.architecture}
                      </Badge>
                    </div>
                    <Separator />

                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        Node.js Version
                      </span>
                      <Badge variant="outline" className="font-mono">
                        {systemInfo.nodeVersion}
                      </Badge>
                    </div>
                    <Separator />

                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">
                        Application Version
                      </span>
                      <Badge variant="secondary" className="font-mono">
                        {systemInfo.appVersion}
                      </Badge>
                    </div>
                    <Separator />

                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Uptime</span>
                      <Badge variant="outline" className="font-mono">
                        {systemInfo.uptime}
                      </Badge>
                    </div>
                    <Separator />

                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium">Memory Usage</span>
                      <Badge variant="outline" className="font-mono">
                        {systemInfo.memoryUsage}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="logs" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-md flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    Application Logs
                  </CardTitle>
                  <CardDescription>
                    Recent system and application logs
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-muted p-3 rounded-md font-mono text-xs h-[200px] overflow-y-auto">
                    <p className="text-muted-foreground">
                      [2023-07-15 08:12:34] INFO: Application started
                    </p>
                    <p className="text-muted-foreground">
                      [2023-07-15 08:13:22] INFO: Connected to database
                    </p>
                    <p className="text-muted-foreground">
                      [2023-07-15 08:15:47] INFO: User authentication successful
                    </p>
                    <p className="text-muted-foreground">
                      [2023-07-15 08:17:12] WARN: High memory usage detected
                    </p>
                    <p className="text-muted-foreground">
                      [2023-07-15 08:19:05] INFO: Cache cleared
                    </p>
                    <p className="text-muted-foreground">
                      [2023-07-15 08:22:31] ERROR: Failed to connect to external
                      API
                    </p>
                    <p className="text-muted-foreground">
                      [2023-07-15 08:25:18] INFO: Retry successful
                    </p>
                    <p className="text-muted-foreground">
                      [2023-07-15 08:30:42] INFO: Scheduled task completed
                    </p>
                  </div>
                  <div className="flex justify-end mt-3">
                    <Button variant="outline" size="sm" className="text-xs">
                      Download Logs
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default DeveloperOptions;
