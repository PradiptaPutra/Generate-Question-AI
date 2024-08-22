"use client"; // Ensure this component runs as a client component

import { useRouter } from 'next/navigation';

export default function LandingPage() {
  const router = useRouter();

  const handleGetStarted = () => {
    router.push('/generator'); // Navigate to the generator page
  };
  

  return (
    <main className="min-h-screen bg-white py-12">
      <div className="container mx-auto px-4">
        <h1 className="text-5xl font-bold text-center mb-8 text-gray-800">
          Effective solution for online exams
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Evaly provides services for creating questions, starting an exam, and analyzing the results of the exam online.
        </p>
        <div className="text-center">
          <button
            className="px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg shadow-md hover:bg-blue-700"
            onClick={handleGetStarted}
          >
            Get started
          </button>
        </div>
      </div>
    </main>
  );
}
