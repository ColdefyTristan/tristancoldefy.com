import { BuildRowRules } from "../types";


export const RULES: BuildRowRules = {
  skinCloseDelta: 2,
  hue: { equalMax: 10, closeMax: 40 },
  buckets: {
    mobility: [
      { name: "I am speed", min: 0, max: 11 },
      { name: "Vite vite", min: 12, max: 47 },
      { name: "ça se débrouille", min: 48, max: 108 },
      { name: "Pas ouf", min: 110, max: 149 },
      { name: "Tristement lent", min: 150, max: 999 },
    ],
    randomness: [
      { name: "Connu",           min: 135, max: 173 }, 
      { name: "C'est ok",        min: 38,  max: 134 }, 
      { name: "Vite fait random",min: 14,  max: 37  }, 
      { name: "Méga random",     min: 1,   max: 13  },
    ],
    cc_quantity: [
      { name: "Horreur", min: 0, max: 16 },
      { name: "Relou", min: 17, max: 43 },
      { name: "C'est ok", min: 44, max: 127 },
      { name: "Anedoctique", min: 128, max: 157 },
      { name: "Absence de CC", min: 158, max: 999 },
    ],
  },
};