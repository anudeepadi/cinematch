import { ReactNode } from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  isLoading?: boolean;
  children: ReactNode;
}

const variants = {
  primary: `
    bg-gradient-to-r from-amber-500 via-orange-500 to-red-500
    text-white font-semibold
    shadow-lg shadow-orange-500/30
    hover:shadow-xl hover:shadow-orange-500/40
    hover:scale-[1.02]
    active:scale-[0.98]
  `,
  secondary: `
    bg-zinc-800/80 backdrop-blur-sm
    text-zinc-100
    border border-zinc-700/50
    hover:bg-zinc-700/80 hover:border-zinc-600/50
    hover:scale-[1.02]
    active:scale-[0.98]
  `,
  ghost: `
    bg-transparent
    text-zinc-400
    hover:text-white hover:bg-white/5
    active:bg-white/10
  `,
  danger: `
    bg-red-600/90
    text-white
    hover:bg-red-500
    shadow-lg shadow-red-500/20
    hover:shadow-xl hover:shadow-red-500/30
  `,
};

const sizes = {
  sm: 'px-4 py-2 text-sm rounded-lg',
  md: 'px-6 py-3 text-base rounded-xl',
  lg: 'px-8 py-4 text-lg rounded-2xl',
};

export function Button({
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  isLoading,
  children,
  className = '',
  disabled,
  ...props
}: ButtonProps) {
  return (
    <motion.button
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      className={`
        inline-flex items-center justify-center gap-2
        font-medium transition-all duration-300 ease-out
        disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
        ${variants[variant]}
        ${sizes[size]}
        ${className}
      `}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <motion.span
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          className="w-5 h-5 border-2 border-current border-t-transparent rounded-full"
        />
      ) : (
        <>
          {icon && iconPosition === 'left' && <span className="flex-shrink-0">{icon}</span>}
          {children}
          {icon && iconPosition === 'right' && <span className="flex-shrink-0">{icon}</span>}
        </>
      )}
    </motion.button>
  );
}
