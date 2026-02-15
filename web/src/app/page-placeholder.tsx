import Link from "next/link";
import { Construction } from 'lucide-react';
export default function PagePlaceholder() {
  return (
    <>
      <Construction />
      <h1>En construction</h1>
      <Construction/>
      <br/>
      <Link href="/">Retour à l’accueil</Link>
    </>
  );
}