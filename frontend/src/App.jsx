import { useState, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import SplashScreen from './components/SplashScreen';
import Questionnaire from './components/Questionnaire';
import SonarScan from './components/SonarScan';
import Zone3Descent from './components/Zone3Descent';
import JobModal from './components/JobModal';

// Flow: splash → questionnaire → scanning → descent (command center + boat + ocean)
export default function App() {
  const [zone, setZone] = useState('splash');
  const [selectedJob, setSelectedJob] = useState(null);
  const [userChoices, setUserChoices] = useState({ domain: null, environment: null, skills: [] });

  const handleSplashComplete = useCallback(() => {
    setZone('questionnaire');
  }, []);

  const handleQuestionnaireComplete = useCallback((choices) => {
    setUserChoices(choices);
    setZone('scanning');
  }, []);

  const handleScanComplete = useCallback(() => {
    setZone('descent');
  }, []);

  const handleSelectJob = useCallback((job) => {
    setSelectedJob(job);
  }, []);

  const handleCloseModal = useCallback(() => {
    setSelectedJob(null);
  }, []);

  return (
    <div className="relative">
      <AnimatePresence mode="wait">
        {zone === 'splash' && (
          <SplashScreen key="splash" onComplete={handleSplashComplete} />
        )}
        {zone === 'questionnaire' && (
          <Questionnaire key="questionnaire" onComplete={handleQuestionnaireComplete} />
        )}
        {zone === 'scanning' && (
          <SonarScan
            key="scanning"
            domain={userChoices.domain}
            onComplete={handleScanComplete}
          />
        )}
        {zone === 'descent' && (
          <Zone3Descent key="descent" onSelectJob={handleSelectJob} />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {selectedJob && (
          <JobModal key="modal" job={selectedJob} onClose={handleCloseModal} />
        )}
      </AnimatePresence>
    </div>
  );
}
