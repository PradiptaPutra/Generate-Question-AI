/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
      return [
        {
          source: '/generate-questions',
          destination: 'http://localhost:5000/generate-questions', // Adjust with your Python server URL
        },
      ];
    },
  };
  
  // Use ES module export syntax
  export default nextConfig;
  