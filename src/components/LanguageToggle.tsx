import { Button } from "@/components/ui/button";
import { useLanguageStore } from "@/hooks/store";

export default function LanguageToggle() {
  const setLanguage = useLanguageStore((state) => state.setLanguage);
  const language = useLanguageStore((state) => state.language);
  return (
    <Button variant="outline" onClick={() => setLanguage((p) => !p)}>
      <span>{language ? "DE" : "EN"} </span>
    </Button>
  );
}
