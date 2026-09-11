import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  transpilePackages: ["@engine/math"],
  experimental: {
    externalDir: true,
  },
};

export default nextConfig;
