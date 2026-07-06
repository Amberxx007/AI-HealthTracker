import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  output: "standalone",
  poweredByHeader: false,
  compress: true,
};

export default nextConfig;
