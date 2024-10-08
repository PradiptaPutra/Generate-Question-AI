"use client"; // Ensure this component runs as a client component
import LandingPage from "@/components/LandingPage";
import QuestionGenerator from "@/components/QuestionGenerator";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-blue-100 to-white py-12">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-8 text-blue-800">
          Pembuat Soal Ujian Indonesia
        </h1>
        {/* You can conditionally render LandingPage or QuestionGenerator based on your routing logic */}
        <LandingPage />
      </div>
    </main>
  );
}
