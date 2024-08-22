"use client"; // Ensure this component runs as a client component

import React, { useState, ChangeEvent, FormEvent } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface FormData {
  subject: string;
  level: string;
  numQuestions: number;
  questionType: 'multiple_choice' | 'essay';
  pdfFile: File | null;
  text: string;
}

interface Question {
  question: string;
  choices?: Array<{ option: string; text: string }>;
  correct_answer?: string;
}

interface ResponseData {
  questions?: Array<Question>;
  error?: string;
}

const QuestionGenerator: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    subject: '',
    level: '',
    numQuestions: 1,
    questionType: 'multiple_choice',
    pdfFile: null,
    text: '',
  });
  const [response, setResponse] = useState<ResponseData | null>(null);
  const [userAnswers, setUserAnswers] = useState<{ [key: number]: string }>({});
  const [loading, setLoading] = useState<boolean>(false);

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prevState => ({ ...prevState, [name]: value }));
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files ? e.target.files[0] : null;
    setFormData(prevState => ({ ...prevState, pdfFile: file }));
  };

  const handleAnswerChange = (questionIndex: number, value: string) => {
    setUserAnswers(prevAnswers => ({
      ...prevAnswers,
      [questionIndex]: value,
    }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    const data = new FormData();
    data.append('subject', formData.subject);
    data.append('level', formData.level);
    data.append('num_questions', formData.numQuestions.toString());
    data.append('question_type', formData.questionType);

    if (formData.pdfFile) {
      data.append('pdf_file', formData.pdfFile);
    } else if (formData.text) {
      data.append('text', formData.text);
    }

    try {
      const res = await fetch('/generate-questions', {
        method: 'POST',
        body: data,
      });
      const result: ResponseData = await res.json();
      setResponse(result);
    } catch (error) {
      console.error('Error:', error);
      setResponse({ error: 'An error occurred while generating questions.' });
    } finally {
      setLoading(false);
    }
  };

  const renderQuestions = () => {
    if (!response?.questions) return null;

    return response.questions.map((question, index) => (
      <div key={index} className="space-y-4">
        <p className="font-semibold">{index + 1}. {question.question}</p>
        {formData.questionType === 'multiple_choice' && question.choices && (
          question.choices.map((choice, choiceIndex) => (
            <div key={choiceIndex} className="flex items-center space-x-2">
              <input
                type="radio"
                id={`question-${index}-choice-${choiceIndex}`}
                name={`question-${index}`}
                value={choice.option}
                onChange={() => handleAnswerChange(index, choice.option)}
              />
              <label htmlFor={`question-${index}-choice-${choiceIndex}`}>
                {choice.text}
              </label>
            </div>
          ))
        )}
        {formData.questionType === 'essay' && (
          <Textarea
            name={`question-${index}`}
            placeholder="Write your answer here..."
            value={userAnswers[index] || ''}
            onChange={(e) => handleAnswerChange(index, e.target.value)}
          />
        )}
      </div>
    ));
  };

  return (
    <div className="container mx-auto p-4">
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">Pembuat Soal Ujian Indonesia</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="subject">Mata Pelajaran</Label>
              <Input
                id="subject"
                name="subject"
                placeholder="Contoh: Matematika"
                value={formData.subject}
                onChange={handleInputChange}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="level">Tingkat Pendidikan</Label>
              <Input
                id="level"
                name="level"
                placeholder="Contoh: SMA Kelas 10"
                value={formData.level}
                onChange={handleInputChange}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="numQuestions">Jumlah Pertanyaan</Label>
              <Input
                id="numQuestions"
                type="number"
                name="numQuestions"
                value={formData.numQuestions}
                onChange={handleInputChange}
                min="1"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="questionType">Jenis Pertanyaan</Label>
              <Select
                name="questionType"
                value={formData.questionType}
                onValueChange={(value: 'multiple_choice' | 'essay') => setFormData(prevState => ({ ...prevState, questionType: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Pilih jenis pertanyaan" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="multiple_choice">Pilihan Ganda</SelectItem>
                  <SelectItem value="essay">Esai</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="pdfFile">Unggah PDF (Opsional)</Label>
              <Input
                id="pdfFile"
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="text">Atau Masukkan Teks</Label>
              <Textarea
                id="text"
                name="text"
                placeholder="Masukkan teks di sini..."
                value={formData.text}
                onChange={handleInputChange}
              />
            </div>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Membuat Soal...' : 'Buat Soal'}
            </Button>
          </form>
        </CardContent>
      </Card>
      {response && (
        <Card className="mt-8 w-full max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Soal yang Dihasilkan:</CardTitle>
          </CardHeader>
          <CardContent>
            {renderQuestions()}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default QuestionGenerator;
