import { ArrowUp, ArrowDown, GripVertical } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ZoneItem {
  zone_id: number;
  zone_name: string;
}

interface ZoneReorderDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  zones: ZoneItem[];
  onReorder: (reorderedZones: ZoneItem[]) => void;
}

export function ZoneReorderDialog({
  open,
  onOpenChange,
  zones,
  onReorder,
}: ZoneReorderDialogProps) {
  const [reorderedZones, setReorderedZones] = useState<ZoneItem[]>(zones);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [dragOverIndex, setDragOverIndex] = useState<number | null>(null);

  // Update local state when zones prop changes or dialog opens
  useEffect(() => {
    if (open) {
      setReorderedZones(zones);
    }
  }, [zones, open]);

  // Mouse-based drag and drop
  const [isDragging, setIsDragging] = useState(false);
  const [dragStartY, setDragStartY] = useState(0);
  const [currentY, setCurrentY] = useState(0);

  const handleMouseDown = (e: React.MouseEvent, index: number) => {
    e.preventDefault();
    setIsDragging(true);
    setDraggedIndex(index);
    setDragStartY(e.clientY);
    setCurrentY(e.clientY);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || draggedIndex === null) return;
    
    setCurrentY(e.clientY);
    
    // Find which item we're over
    const items = document.querySelectorAll('[data-zone-item]');
    let newDragOverIndex: number | null = null;
    
    items.forEach((item, idx) => {
      const rect = item.getBoundingClientRect();
      if (e.clientY >= rect.top && e.clientY <= rect.bottom) {
        newDragOverIndex = idx;
      }
    });
    
    setDragOverIndex(newDragOverIndex);
  };

  const handleMouseUp = () => {
    if (!isDragging || draggedIndex === null) return;
    
    if (dragOverIndex !== null && draggedIndex !== dragOverIndex) {
      const newZones = [...reorderedZones];
      const [draggedZone] = newZones.splice(draggedIndex, 1);
      newZones.splice(dragOverIndex, 0, draggedZone);
      setReorderedZones(newZones);
    }
    
    setIsDragging(false);
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  // HTML5 drag and drop as primary method
  const handleDragStart = (e: React.DragEvent, index: number) => {
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", index.toString());
    // Create a custom drag image
    const dragImage = e.currentTarget.cloneNode(true) as HTMLElement;
    dragImage.style.opacity = "0.5";
    document.body.appendChild(dragImage);
    dragImage.style.position = "absolute";
    dragImage.style.top = "-1000px";
    e.dataTransfer.setDragImage(dragImage, e.clientX - e.currentTarget.getBoundingClientRect().left, e.clientY - e.currentTarget.getBoundingClientRect().top);
    setTimeout(() => document.body.removeChild(dragImage), 0);
    
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();
    e.stopPropagation();
    e.dataTransfer.dropEffect = "move";
    
    if (draggedIndex !== null && draggedIndex !== index) {
      setDragOverIndex(index);
    }
  };

  const handleDragLeave = () => {
    // Don't clear immediately to prevent flickering
  };

  const handleDrop = (e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (draggedIndex === null || draggedIndex === dropIndex) {
      setDraggedIndex(null);
      setDragOverIndex(null);
      return;
    }

    const newZones = [...reorderedZones];
    const [draggedZone] = newZones.splice(draggedIndex, 1);
    newZones.splice(dropIndex, 0, draggedZone);

    setReorderedZones(newZones);
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
    setDragOverIndex(null);
  };

  // Move zone up or down
  const moveZone = (index: number, direction: "up" | "down") => {
    if (
      (direction === "up" && index === 0) ||
      (direction === "down" && index === reorderedZones.length - 1)
    ) {
      return;
    }

    const newZones = [...reorderedZones];
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    [newZones[index], newZones[targetIndex]] = [
      newZones[targetIndex],
      newZones[index],
    ];
    setReorderedZones(newZones);
  };

  const handleSave = () => {
    onReorder(reorderedZones);
    onOpenChange(false);
  };

  const handleCancel = () => {
    setReorderedZones(zones);
    setDraggedIndex(null);
    setDragOverIndex(null);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className="max-w-md"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <DialogHeader>
          <DialogTitle>Reorder Zones</DialogTitle>
          <DialogDescription>
            Drag zones to reorder them, or use the arrow buttons. The order will be saved and applied to the dashboard.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {reorderedZones.map((zone, index) => (
            <div
              key={zone.zone_id}
              data-zone-item
              draggable={true}
              onDragStart={(e) => handleDragStart(e, index)}
              onDragOver={(e) => handleDragOver(e, index)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, index)}
              onDragEnd={handleDragEnd}
              onMouseDown={(e) => handleMouseDown(e, index)}
              style={{
                opacity: draggedIndex === index ? 0.5 : 1,
                transform: dragOverIndex === index ? "translateY(-2px) scale(1.01)" : "translateY(0) scale(1)",
                transition: draggedIndex === index ? "none" : "all 0.2s ease",
                cursor: isDragging && draggedIndex === index ? "grabbing" : "grab",
              }}
              className={`
                flex items-center gap-3 p-3 rounded-lg border
                select-none touch-none
                ${
                  dragOverIndex === index
                    ? "border-primary bg-primary/10 shadow-md z-10 relative"
                    : "border-border bg-card/50 hover:bg-card/80"
                }
                ${draggedIndex === index ? "shadow-lg" : ""}
              `}
            >
              <div className="flex items-center gap-1">
                <GripVertical className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                <div className="flex flex-col gap-0.5">
                  <button
                    type="button"
                    onClick={() => moveZone(index, "up")}
                    disabled={index === 0}
                    className="p-0.5 hover:bg-accent rounded disabled:opacity-30 disabled:cursor-not-allowed"
                    aria-label="Move up"
                  >
                    <ArrowUp className="h-3 w-3" />
                  </button>
                  <button
                    type="button"
                    onClick={() => moveZone(index, "down")}
                    disabled={index === reorderedZones.length - 1}
                    className="p-0.5 hover:bg-accent rounded disabled:opacity-30 disabled:cursor-not-allowed"
                    aria-label="Move down"
                  >
                    <ArrowDown className="h-3 w-3" />
                  </button>
                </div>
              </div>
              <span className="flex-1 text-sm font-medium">{zone.zone_name}</span>
            </div>
          ))}
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave}>Save Order</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
