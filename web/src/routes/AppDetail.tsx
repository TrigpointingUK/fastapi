import { useParams } from "react-router-dom";

export default function AppDetail() {
  const { id } = useParams<{ id: string }>();

  return (
    <div>
      <h1>Trig Point Details</h1>
      <p>This is your friendly /app/ page, giving you full details of {id}</p>
    </div>
  );
}

