

export type DiagramNode = {
  key: string;
  title: string;
  href: `#${string}`;
  variant?: "browser" | "proxy" | "next" | "api" | "db";
};

