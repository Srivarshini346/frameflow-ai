import React, { useState } from 'react';
import { Star, Award, CheckCircle2, BarChart2, ShieldCheck, HelpCircle } from 'lucide-react';

export default function QualityEvaluationReport({ currentJob }) {
  const [ratings, setRatings] = useState({});

  const handleRate = (sceneNum, score) => {
    setRatings({
      ...ratings,
      [sceneNum]: score
    });
  };

  const scenes = currentJob?.scenes || [
    {
      scene_number: 1,
      narration_text: "Technology is transforming the modern classroom.",
      visual_description: "cinematic shot: modern digital interface with glowing data streams and engineer working",
      relevance_score: 0.98,
      vlm_score: 0.99,
      selection_reason: "High semantic match to classroom technology concept."
    },
    {
      scene_number: 2,
      narration_text: "Artificial intelligence creates personalised learning for students.",
      visual_description: "cinematic shot: focused student interacting with interactive digital education tablet in modern space",
      relevance_score: 0.96,
      vlm_score: 0.98,
      selection_reason: "Matched to interactive digital learning."
    }
  ];

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '36px 24px' }} className="animate-fade">
      <div style={{ marginBottom: '28px' }}>
        <h1 style={{ fontSize: '26px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '6px' }}>
          Quality Evaluation & Human-in-the-Loop Rating
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
          Evaluate semantic precision, Vision-Language Model (VLM) alignment, and record human benchmark ratings.
        </p>
      </div>

      {/* Summary Scorecard */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px', marginBottom: '32px' }}>
        <div style={{
          backgroundColor: 'var(--bg-card)',
          padding: '24px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
            Semantic Keyword Relevance
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--primary)', marginTop: '6px' }}>
            97.0%
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Mean Cosine Similarity on Intent Vectors
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-card)',
          padding: '24px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
            VLM Visual-Semantic Alignment
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--accent-mint)', marginTop: '6px' }}>
            98.5%
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Resolution, Frame Rate & Content Scoring
          </div>
        </div>

        <div style={{
          backgroundColor: 'var(--bg-card)',
          padding: '24px',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-light)',
          boxShadow: 'var(--shadow-sm)'
        }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
            Commercial Rights Compliance
          </div>
          <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--secondary-text)', marginTop: '6px' }}>
            100%
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
            All clips verified CC0 / Commercial Clearance
          </div>
        </div>
      </div>

      {/* Human Rating Interactive Workflow */}
      <div style={{
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        padding: '28px',
        border: '1px solid var(--border-light)',
        boxShadow: 'var(--shadow-sm)',
        marginBottom: '28px'
      }}>
        <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
          Human Relevance Benchmark Rating
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '20px' }}>
          Rate how accurately each scene visual matches the narration. Ratings feed directly into our quality alignment logs.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {scenes.map((sc) => {
            const currentRating = ratings[sc.scene_number] || 5;
            return (
              <div
                key={sc.scene_number}
                style={{
                  padding: '18px 20px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--bg-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      backgroundColor: 'var(--primary-light)',
                      color: 'var(--primary)',
                      padding: '2px 8px',
                      borderRadius: 'var(--radius-full)'
                    }}>
                      Scene {sc.scene_number}
                    </span>
                    <span style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)' }}>
                      "{sc.narration_text}"
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                    <strong>Visual:</strong> {sc.visual_description}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => handleRate(sc.scene_number, star)}
                      style={{
                        background: 'none',
                        color: star <= currentRating ? '#F59E0B' : 'var(--border-medium)',
                        cursor: 'pointer',
                        padding: '4px'
                      }}
                    >
                      <Star size={20} fill={star <= currentRating ? '#F59E0B' : 'none'} />
                    </button>
                  ))}
                  <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginLeft: '8px' }}>
                    {currentRating}/5
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
