import { ConditionOut } from '../types';
import { getCategoryDisplay } from '../lib/categoryLabels';
import styles from './MtgDoku.module.css';

type Props = { condition: ConditionOut };

export default function ConditionPill({ condition }: Props) {
  const { text, icons } = getCategoryDisplay(condition.id);

  return (
    <span className={styles.pill}>
      {icons.map((classes, i) => (
        <i key={i} className={classes.join(' ')} aria-hidden="true" />
      ))}
      {icons.length > 0 && <span className={styles.pillSep} />}
      {text}
    </span>
  );
}
