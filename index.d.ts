type LocaleText = { es: string; en: string; ru: string }

export type QuestionResponse = {
  text: LocaleText
  correct?: boolean
}

export type Question = {
  text: LocaleText
  img?: string | null
  responses: QuestionResponse[]
  explanation: { text: LocaleText }
  citation?: string
}

export declare const questions: Question[]
export declare const questionImages: { [key: string]: number }
