import { motion } from "framer-motion"
import { Link } from "react-router-dom"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Archive, ChevronRight } from "lucide-react"
import { zoneNameMapping } from "@/lib/zoneNameMapping"
import { Badge } from "./ui/badge"
import { Archive as typeArchive } from "@/hooks/store"
const SinglePaletteArchives = ({zoneIDs,archives}:{zoneIDs:number[],archives:typeArchive[]}) => {
  return (
    zoneIDs.map((zoneID) => (
     <motion.div variants={{
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 260,
        damping: 20,
      },
    },
  }} key={zoneID}>
          <Link to={`/details/${zoneID}`} className="block h-full">
            <Card className="group h-full overflow-hidden border border-border/50 bg-card/30 backdrop-blur-sm transition-all duration-300 hover:bg-card/80 hover:shadow-lg hover:shadow-primary/5 dark:hover:shadow-primary/10">
              <CardHeader className="border-b p-6 bg-gradient-to-r from-muted/80 to-muted/30 transition-colors duration-300 group-hover:from-primary/10 group-hover:to-primary/5">
                <CardTitle className="flex items-center text-xl">
                  <div className="mr-3 flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-primary transition-transform duration-300 group-hover:scale-110">
                    <Archive className="h-4 w-4" />
                  </div>
                  <span className="transition-colors duration-300 group-hover:text-primary">
                    {zoneNameMapping[zoneID]}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <CardDescription className="text-sm font-medium dark:text-white">
                      <span className="text-muted-foreground">Palette:</span> 1
                    </CardDescription>
                    <Badge
                      variant="outline"
                      className="bg-background/50 transition-colors duration-300 group-hover:bg-primary/10 group-hover:text-primary"
                    >
                      Aktiv
                    </Badge>
                  </div>

                  <div className="space-y-2">
                    <div className="text-xs text-muted-foreground">
                      Proben je Palette:
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge
                        variant="secondary"
                        className="transition-all duration-300 group-hover:bg-primary/20"
                      >
                        {archives.find((archive) => archive.zone_id === zoneID)
                          ?.zone.zone_items.length ?? "0"}
                      </Badge>
                    </div>
                  </div>

                  <div className="flex items-center justify-end text-xs text-muted-foreground">
                    <span className="mr-1">Details anzeigen</span>
                    <ChevronRight className="h-3 w-3 transition-transform duration-300 group-hover:translate-x-1" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        </motion.div>
    )))
}

export default SinglePaletteArchives
