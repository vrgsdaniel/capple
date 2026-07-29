import * as React from "react"
import { AlertDialog as Primitive } from "radix-ui"
import { cn } from "@/lib/utils"
import { buttonVariants } from "@/components/ui/button-variants"

const AlertDialog = Primitive.Root
const AlertDialogTrigger = Primitive.Trigger

const AlertDialogOverlay = React.forwardRef<
  React.ComponentRef<typeof Primitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof Primitive.Overlay>
>(({ className, ...props }, ref) => (
  <Primitive.Overlay
    ref={ref}
    className={cn(
      "fixed inset-0 z-50 bg-black/50",
      "data-[state=open]:animate-in data-[state=closed]:animate-out",
      "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  />
))
AlertDialogOverlay.displayName = "AlertDialogOverlay"

const AlertDialogContent = React.forwardRef<
  React.ComponentRef<typeof Primitive.Content>,
  React.ComponentPropsWithoutRef<typeof Primitive.Content>
>(({ className, ...props }, ref) => (
  <Primitive.Portal>
    <AlertDialogOverlay />
    <Primitive.Content
      ref={ref}
      className={cn(
        "fixed left-1/2 top-1/2 z-50 w-full max-w-sm -translate-x-1/2 -translate-y-1/2",
        "rounded-xl border border-border bg-card p-6 shadow-xl",
        "data-[state=open]:animate-in data-[state=closed]:animate-out",
        "data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
        "data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95",
        className
      )}
      {...props}
    />
  </Primitive.Portal>
))
AlertDialogContent.displayName = "AlertDialogContent"

function AlertDialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col gap-2 mb-5", className)} {...props} />
}

function AlertDialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col-reverse gap-2 sm:flex-row sm:justify-end", className)} {...props} />
}

const AlertDialogTitle = React.forwardRef<
  React.ComponentRef<typeof Primitive.Title>,
  React.ComponentPropsWithoutRef<typeof Primitive.Title>
>(({ className, ...props }, ref) => (
  <Primitive.Title ref={ref} className={cn("text-base font-semibold", className)} {...props} />
))
AlertDialogTitle.displayName = "AlertDialogTitle"

const AlertDialogDescription = React.forwardRef<
  React.ComponentRef<typeof Primitive.Description>,
  React.ComponentPropsWithoutRef<typeof Primitive.Description>
>(({ className, ...props }, ref) => (
  <Primitive.Description ref={ref} className={cn("text-sm text-muted-foreground", className)} {...props} />
))
AlertDialogDescription.displayName = "AlertDialogDescription"

const AlertDialogAction = React.forwardRef<
  React.ComponentRef<typeof Primitive.Action>,
  React.ComponentPropsWithoutRef<typeof Primitive.Action>
>(({ className, ...props }, ref) => (
  <Primitive.Action ref={ref} className={cn(buttonVariants(), className)} {...props} />
))
AlertDialogAction.displayName = "AlertDialogAction"

const AlertDialogCancel = React.forwardRef<
  React.ComponentRef<typeof Primitive.Cancel>,
  React.ComponentPropsWithoutRef<typeof Primitive.Cancel>
>(({ className, ...props }, ref) => (
  <Primitive.Cancel ref={ref} className={cn(buttonVariants({ variant: "outline" }), className)} {...props} />
))
AlertDialogCancel.displayName = "AlertDialogCancel"

export {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
}
