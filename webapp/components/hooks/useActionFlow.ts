"use client";

import { useCallback, useRef, useState } from "react";

import { useToast } from "@/components/providers/ToastProvider";

type OptimisticUpdater = () => void | (() => void);

export type RunActionOptions = {
  id?: string;
  label: string;
  successMessage?: string;
  errorMessage?: string;
  optimisticUpdate?: OptimisticUpdater;
  handler?: () => Promise<unknown>;
  undoLabel?: string;
};

type LastAction = {
  id: string;
  label: string;
  rollback: () => void;
};

export function useActionFlow() {
  const { pushToast } = useToast();
  const [lastAction, setLastAction] = useState<LastAction | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const idCounter = useRef(0);

  const notifyUndo = useCallback(
    (message = "Action undone") => {
      pushToast({
        title: message,
      });
    },
    [pushToast]
  );

  const undoById = useCallback(
    (id: string) => {
      setLastAction((current) => {
        if (!current || current.id !== id) {
          return current;
        }
        current.rollback();
        notifyUndo();
        return null;
      });
    },
    [notifyUndo]
  );

  const runAction = useCallback(
    async ({
      id,
      label,
      successMessage,
      errorMessage,
      optimisticUpdate,
      handler,
      undoLabel,
    }: RunActionOptions) => {
      const actionId = id ?? `action-${++idCounter.current}`;
      setIsRunning(true);
      const rollback = optimisticUpdate?.();

      try {
        await (handler ? handler() : Promise.resolve());
        if (typeof rollback === "function") {
          setLastAction({ id: actionId, label: undoLabel ?? label, rollback });
        } else {
          setLastAction(null);
        }
        pushToast({
          title: successMessage ?? `${label} completed`,
          variant: "success",
          action:
            typeof rollback === "function"
              ? {
                  label: "Undo",
                  onClick: () => undoById(actionId),
                }
              : undefined,
        });
      } catch (error) {
        if (typeof rollback === "function") {
          rollback();
        }
        setLastAction(null);
        pushToast({
          title: errorMessage ?? `${label} failed`,
          variant: "error",
        });
        throw error;
      } finally {
        setIsRunning(false);
      }
    },
    [pushToast, undoById]
  );

  const undoLastAction = useCallback(() => {
    setLastAction((current) => {
      if (!current) {
        return current;
      }
      current.rollback();
      notifyUndo();
      return null;
    });
  }, [notifyUndo]);

  return {
    runAction,
    undoLastAction,
    canUndo: Boolean(lastAction),
    isRunning,
    lastActionLabel: lastAction?.label,
  };
}
