!(import! &self utils)
!(import! &self tvconsistency)
;Formulas

(= (mp-formula (STV $abs $abc) (STV $as $ac)) (STV (* $abs $as) (min-atom ($abc $ac))))

(= (precise-mp-formula (STV $nabs $nabc) (STV $abs $abc) (STV $as $ac)) (STV (+ (* $abs $as) (* $nabs (- 1.0 $as))) (min-atom ($nabc $abc $ac))))

(= (and-formula (STV $as $ac) (STV $bs $bc)) (STV (* $as $bs) (min-atom ($ac $bc))))
(= (or-formula (STV $as $ac) (STV $bs $bc)) (STV (max-atom ($as $bs)) (min-atom ($ac $bc))))

(= (mp-formula (STV $abs $abc) (STV $as $ac)) (STV (* $abs $as) (min-atom ($abc $ac))))

;(= (inversion-formula (STV $as $ac) (STV $bs $bc) (STV $abs $abc))
;  (STV (/ (* $as $abs) $bs) (* 0.9 (min-atom ($ac $bc $abc)))))

(= (inversion-formula $stva $stvb $stvab)
  (let ((STV $as $ac) (STV $bs $bc) (STV $abs $abc)) (ensure-tv-consistency ($stva $stvb $stvab))
  (STV (/ (* $as $abs) $bs) (* 0.9 (min-atom ($ac $bc $abc))))))

(= (merge-counts $count1 $count2) (+ $count1 $count2))

(= (mean-update $m1 $m2 $c1 $c2) (/ (+ (* $m1 $c1) (* $m2 $c2)) (+ $c1 $c2)))

!(assertEqual (mean-update 0.9 0.9 1 1) 0.9)

(= (mergetvs (STV $m1 $conf1) (STV $m2 $conf2))
   (let* (($count1 (confidence-to-count $conf1))
          ($count2 (confidence-to-count $conf2))
          ($m (mean-update $m1 $m2 $count1 $count2))
          ($c (merge-counts $count1 $count2))
          ($conf (count-to-confidence $c))
          )
            (STV $m $conf)
         ))

!(assertEqual (mergetvs (STV 0.9 0.9) (STV 0.9 0.9)) (STV 0.9 0.9473684210526316))

(= (stv< (STV $s1 $c1) (STV $s2 $c2)) (< $s1 $s2))

;!(ensure-tv-consistency ((STV 0.5 0.1) (STV 0.1 0.1) (STV 0.9 0.1)))

!(inversion-formula (STV 0.5 0.1) (STV 0.1 0.1) (STV 0.9 0.1))
