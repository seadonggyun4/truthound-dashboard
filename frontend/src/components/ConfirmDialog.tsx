/**
 * Reusable confirmation dialog component and hook.
 *
 * Usage (Global - recommended):
 *   import { confirm } from '@/components/ConfirmDialog'
 *
 *   const handleDelete = async () => {
 *     const confirmed = await confirm({
 *       title: 'Delete item?',
 *       description: 'This action cannot be undone.',
 *       confirmText: 'Delete',
 *       variant: 'destructive',
 *     })
 *     if (confirmed) {
 *       // proceed with deletion
 *     }
 *   }
 *
 * Usage (Hook - for custom behavior):
 *   const { confirm, ConfirmDialog } = useConfirm()
 *   // ... same as above but with local state
 */

import { useState, useCallback, createContext, useContext } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { cn } from '@/lib/utils'
import { buttonVariants } from '@/components/ui/button'
import { str } from '@/lib/intlayer-utils'

export interface ConfirmOptions {
  title: string
  description?: string
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'destructive'
}

interface ConfirmState extends ConfirmOptions {
  isOpen: boolean
  resolve: ((value: boolean) => void) | null
}

export function useConfirm() {
  const common = useSafeIntlayer('common')
  const [state, setState] = useState<ConfirmState>({
    isOpen: false,
    title: '',
    description: '',
    confirmText: '',
    cancelText: '',
    variant: 'default',
    resolve: null,
  })

  const confirm = useCallback(
    (options: ConfirmOptions): Promise<boolean> => {
      return new Promise((resolve) => {
        setState({
          isOpen: true,
          title: options.title,
          description: options.description,
          confirmText: options.confirmText || str(common.confirm),
          cancelText: options.cancelText || str(common.cancel),
          variant: options.variant || 'default',
          resolve,
        })
      })
    },
    [common]
  )

  const handleConfirm = useCallback(() => {
    state.resolve?.(true)
    setState((prev) => ({ ...prev, isOpen: false, resolve: null }))
  }, [state.resolve])

  const handleCancel = useCallback(() => {
    state.resolve?.(false)
    setState((prev) => ({ ...prev, isOpen: false, resolve: null }))
  }, [state.resolve])

  const ConfirmDialogComponent = useCallback(
    () => (
      <AlertDialog open={state.isOpen} onOpenChange={(open) => !open && handleCancel()}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{state.title}</AlertDialogTitle>
            {state.description && (
              <AlertDialogDescription>{state.description}</AlertDialogDescription>
            )}
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={handleCancel}>
              {state.cancelText}
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirm}
              className={cn(
                state.variant === 'destructive' &&
                  buttonVariants({ variant: 'destructive' })
              )}
            >
              {state.confirmText}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    ),
    [state, handleConfirm, handleCancel]
  )

  return {
    confirm,
    ConfirmDialog: ConfirmDialogComponent,
  }
}

export default useConfirm

// ============================================
// Global confirm function (no hook required)
// ============================================

type ConfirmResolver = (value: boolean) => void

interface GlobalConfirmState {
  isOpen: boolean
  options: ConfirmOptions
  resolve: ConfirmResolver | null
}

let globalState: GlobalConfirmState = {
  isOpen: false,
  options: { title: '' },
  resolve: null,
}

let listeners: Set<() => void> = new Set()

function notifyListeners() {
  listeners.forEach((listener) => listener())
}

/**
 * Global confirm function - can be called from anywhere without hooks
 */
export function confirm(options: ConfirmOptions): Promise<boolean> {
  return new Promise((resolve) => {
    globalState = {
      isOpen: true,
      options,
      resolve,
    }
    notifyListeners()
  })
}

function handleGlobalConfirm() {
  globalState.resolve?.(true)
  globalState = { ...globalState, isOpen: false, resolve: null }
  notifyListeners()
}

function handleGlobalCancel() {
  globalState.resolve?.(false)
  globalState = { ...globalState, isOpen: false, resolve: null }
  notifyListeners()
}

/**
 * Global ConfirmDialog component - mount once in App.tsx
 */
export function GlobalConfirmDialog() {
  const common = useSafeIntlayer('common')
  const [, forceUpdate] = useState({})

  // Subscribe to global state changes
  useState(() => {
    const listener = () => forceUpdate({})
    listeners.add(listener)
    return () => listeners.delete(listener)
  })

  const { isOpen, options } = globalState
  const {
    title,
    description,
    confirmText,
    cancelText,
    variant = 'default',
  } = options

  return (
    <AlertDialog open={isOpen} onOpenChange={(open) => !open && handleGlobalCancel()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          {description && (
            <AlertDialogDescription>{description}</AlertDialogDescription>
          )}
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleGlobalCancel}>
            {cancelText || str(common.cancel)}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleGlobalConfirm}
            className={cn(
              variant === 'destructive' && buttonVariants({ variant: 'destructive' })
            )}
          >
            {confirmText || str(common.confirm)}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
