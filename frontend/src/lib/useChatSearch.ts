import { useSyncExternalStore } from "react";
import {
  getChatSearchState,
  subscribeChatSearch,
  type ChatSearchState,
} from "./chatSearchResults";

export function useChatSearch(): ChatSearchState | null {
  return useSyncExternalStore(subscribeChatSearch, getChatSearchState, getChatSearchState);
}
