import { InputHTMLAttributes, forwardRef, ReactNode } from 'react';
import { motion } from 'framer-motion';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, iconPosition = 'left', className = '', ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-zinc-400 mb-2 tracking-wide">
            {label}
          </label>
        )}
        <div className="relative group">
          {icon && iconPosition === 'left' && (
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-amber-500 transition-colors">
              {icon}
            </span>
          )}
          <input
            ref={ref}
            className={`
              w-full px-4 py-3.5
              ${icon && iconPosition === 'left' ? 'pl-12' : ''}
              ${icon && iconPosition === 'right' ? 'pr-12' : ''}
              bg-zinc-900/60 backdrop-blur-sm
              border-2 border-zinc-800
              rounded-xl
              text-white placeholder-zinc-600
              outline-none
              transition-all duration-300
              focus:border-amber-500/50 focus:bg-zinc-900/80
              focus:shadow-lg focus:shadow-amber-500/10
              hover:border-zinc-700
              ${error ? 'border-red-500/50 focus:border-red-500/50' : ''}
              ${className}
            `}
            {...props}
          />
          {icon && iconPosition === 'right' && (
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-500 group-focus-within:text-amber-500 transition-colors">
              {icon}
            </span>
          )}

          {/* Glow effect on focus */}
          <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-amber-500/0 via-amber-500/0 to-orange-500/0 opacity-0 group-focus-within:opacity-100 blur-xl transition-opacity -z-10" />
        </div>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-2 text-sm text-red-400"
          >
            {error}
          </motion.p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
