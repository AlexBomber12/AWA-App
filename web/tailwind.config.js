import { shadcnPreset } from '@shadcn/ui/preset'

export default {
  presets: [shadcnPreset],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
