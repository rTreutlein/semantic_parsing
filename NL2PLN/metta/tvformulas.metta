!(import! &self utils)
;Formulas

!(bind! K 800)

(= (mp-formula (STV $abs $abc) (STV $as $ac)) (STV (* $abs $as) (min-atom ($abc $ac))))

(= (precise-mp-formula (STV $nabs $nabc) (STV $abs $abc) (STV $as $ac)) (STV (+ (* $abs $as) (* $nabs (- 1.0 $as))) (min-atom ($nabc $abc $ac))))

(= (and-formula (STV $as $ac) (STV $bs $bc)) (STV (* $as $bs) (min-atom ($ac $bc))))
(= (or-formula (STV $as $ac) (STV $bs $bc)) (STV (max-atom ($as $bs)) (min-atom ($ac $bc))))

(= (mp-formula (STV $abs $abc) (STV $as $ac)) (STV (* $abs $as) (min-atom ($abc $ac))))

(= (inversion-formula (STV $as $ac) (STV $bs $bc) (STV $abs $abc)) (STV (/ (* $as $abs) $bs) (* 0.9 (min-atom ($ac $bc $abc)))))

(= (inversion-mp-formula (STV $as $ac) (STV $bs $bc) (STV $abs $abc)) (STV (* $as $abs) (min-atom ($ac $bc $abc))))

(= (confidenc-to-count $conf) (/ (* $conf K) (- 1 $conf)))

(= (count-to-confidenc $count) (/ $count (+ $count K)))

!(assertEqual (confidenc-to-count 0.9) 7200.000000000002)

!(assertEqual (count-to-confidenc 400.0) 0.3333333333333333)

(= (merge-counts $count1 $count2) (+ $count1 $count2))

(= (mean-update $m1 $m2 $c1 $c2) (/ (+ (* $m1 $c1) (* $m2 $c2)) (+ $c1 $c2)))

(= (STV-to-bettadist (STV $s $conf)) (let $cnt (confidenc-to-count $conf) (betadist (* $s $cnt) (* $cnt (- 1 $s)))))

!(assertEqual (mean-update 0.9 0.9 1 1) 0.9)

(= (mergetvs (STV $m1 $conf1) (STV $m2 $conf2))
   (let* (($count1 (confidenc-to-count (min-atom ($conf1 0.999))))
          ($count2 (confidenc-to-count (min-atom ($conf2 0.999))))
          ($m (mean-update $m1 $m2 $count1 $count2))
          ($c (merge-counts $count1 $count2))
          ($conf (count-to-confidenc $c))
          )
            (STV $m $conf)
         ))

!(assertEqual (mergetvs (STV 0.9 0.9) (STV 0.9 0.9)) (STV 0.9 0.9473684210526316))

(= (stv< (STV $s1 $c1) (STV $s2 $c2)) (< $s1 $s2))
