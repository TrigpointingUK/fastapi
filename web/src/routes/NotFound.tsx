import { Link } from "react-router-dom";
import Layout from "../components/layout/Layout";
import Button from "../components/ui/Button";

export default function NotFound() {
  return (
    <Layout>
      <div className="text-center py-12">
        <div className="text-6xl mb-4">🧭</div>
        <h1 className="text-4xl font-bold text-gray-800 mb-4">404 - Not Found</h1>
        <p className="text-gray-600 mb-6">
          The page you're looking for doesn't exist.
        </p>
        <Link to="/">
          <Button variant="primary">Return Home</Button>
        </Link>
      </div>
    </Layout>
  );
}

