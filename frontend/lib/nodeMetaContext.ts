"use client";

import { createContext, useContext } from "react";

import type { NodeTypeMeta } from "@/lib/types";

export const NodeMetaContext = createContext<Map<string, NodeTypeMeta>>(new Map());

export function useNodeMeta(): Map<string, NodeTypeMeta> {
  return useContext(NodeMetaContext);
}