!(import! &self utils)

(= (compute-mean $alpha $beta) (/ $alpha (+ $alpha $beta)))

(= (adjust-beta-distributions ((Beta $alpha_a $beta_a) (Beta $alpha_b $beta_b) (Beta $alpha_ab $beta_ab)))
  ;; Define helper functions
  ;; Base case: if condition holds, return parameters
  (let* (($pa (compute-mean $alpha_a $beta_a))
         ($pb (compute-mean $alpha_b $beta_b))
         ($paimpliesb (compute-mean $alpha_ab $beta_ab))
         ($Lunbond (- (+ $pa $pb) 1))
         ($L (max-atom (0 $Lunbond)))
         ($R (* $pa $paimpliesb))
         ($gap (- $L $R))
        )
  (if (<= $gap 0)
      ((Beta $alpha_a $beta_a) (Beta $alpha_b $beta_b) (Beta $alpha_ab $beta_ab))
      ;; Recursive case: adjust parameters and recurse
      (let* (;; Compute weights
             ($wa (* (- 1 $paimpliesb) (/ 1 (+ $alpha_a $beta_a))))
             ($wb (/ 1 (+ $alpha_b $beta_b)))
             ($wab (* $pa (/ 1 (+ $alpha_ab $beta_ab))))
             ($total-w (+ $wa (+ $wb $wab)))
             ;; Normalize to proportions
             ($prop_a (if (== $total-w 0.0) 0.0 (/ $wa $total-w)))
             ($prop_b (if (== $total-w 0.0) 0.0 (/ $wb $total-w)))
             ($prop_ab (if (== $total-w 0.0) 0.0 (/ $wab $total-w)))
             ;; Total counts to remove per iteration
             ($adjustment_factor 1) ;;Lower factor for better accuary but slower convergence
             ($total_evidence (+ (+ $alpha_a $beta_a) (+ (+ $alpha_b $beta_b) (+ $alpha_ab $beta_ab))))                                                                                   
             ($n_estimate (* $gap (* $total_evidence $adjustment_factor)))
             ($n (max-atom (1 $n_estimate)))
             ;; Calculate removals, ensure at least some change
             ($remove_a (* $n $prop_a))
             ($remove_b (* $n $prop_b))
             ($remove_ab (* $n $prop_ab))
             ;; New parameters (ensure non-negative)
             ($new_alpha_a (- $alpha_a $remove_a))
             ($new_alpha_b (- $alpha_b $remove_b))
             ($new_beta_ab (- $beta_ab $remove_ab)))
        ;; Recursive call with updated parameters
        (adjust-beta-distributions ((Beta $new_alpha_a $beta_a)
                                    (Beta $new_alpha_b $beta_b)
                                    (Beta $alpha_ab $new_beta_ab)))))))


(= (adjust-beta-distributions2 ((Beta $alpha_a $beta_a) (Beta $alpha_b $beta_b) (Beta $alpha_ab $beta_ab)))
  ;; Compute variables
  (let* (($pa (compute-mean $alpha_a $beta_a))
         ($pb (compute-mean $alpha_b $beta_b))
         ($paimpliesb (compute-mean $alpha_ab $beta_ab))
         ($R (* $pa $paimpliesb))
         ($gap (- $R $pb)))
    ;; Base case: if condition holds, return parameters
    (if (<= $gap 0)
        ((Beta $alpha_a $beta_a) (Beta $alpha_b $beta_b) (Beta $alpha_ab $beta_ab))
        ;; Recursive case: adjust parameters by deleting evidence
        (let* (($wa (* $paimpliesb (/ 1 (+ $alpha_a $beta_a))))  ;; Decrease $pa via $alpha_a
               ($wb (/ 1 (+ $alpha_b $beta_b)))                  ;; Increase $pb via $beta_b
               ($wab (* $pa (/ 1 (+ $alpha_ab $beta_ab))))       ;; Decrease $paimpliesb via $alpha_ab
               ($total-w (+ $wa (+ $wb $wab)))
               ;; Normalize proportions
               ($prop_a (if (== $total-w 0.0) 0.0 (/ $wa $total-w)))
               ($prop_b (if (== $total-w 0.0) 0.0 (/ $wb $total-w)))
               ($prop_ab (if (== $total-w 0.0) 0.0 (/ $wab $total-w)))
               ;; Total counts to remove per iteration
               ($adjustment_factor 1) ;;Lower factor for better accuary but slower convergence
               ($total_evidence (+ (+ $alpha_a $beta_a) (+ (+ $alpha_b $beta_b) (+ $alpha_ab $beta_ab))))                                                                                   
               ($n_estimate (* $gap (* $total_evidence $adjustment_factor)))
               ($n (max-atom (1 $n_estimate)))
               ;($n 5)
               ;; Calculate removals
               ($remove_a (* $n $prop_a))
               ($remove_b (* $n $prop_b))
               ($remove_ab (* $n $prop_ab))
               ;; New parameters: only decrease
               ($new_alpha_a (- $alpha_a $remove_a))  ;; Decrease $pa
               ($new_beta_b (- $beta_b $remove_b))    ;; Increase $pb
               ($new_alpha_ab (- $alpha_ab $remove_ab)) ;; Decrease $paimpliesb
              )
          ;; Recursive call
          (adjust-beta-distributions2 ((Beta $new_alpha_a $beta_a)
                                       (Beta $alpha_b $new_beta_b)
                                       (Beta $new_alpha_ab $beta_ab)))))))


!(bind! K 800)

(= (confidence-to-count $conf) (/ (* $conf K) (- 1 (min-atom ($conf 0.9999)))))

(= (count-to-confidence $count) (/ $count (+ $count K)))

!(assertEqual (confidence-to-count 0.9) 7200.000000000002)

!(assertEqual (count-to-confidence 400.0) 0.3333333333333333)

;(: STV (-> Number Number STV))
;(: Beta (-> Number Number Beta))

;(: stv-to-beta (-> STV Beta))  ; Type: Takes STV expression, returns Beta expression
(= (stv-to-beta (STV $s $c))
   (let $n (confidence-to-count $c)          ; Convert confidence to count
     (let $alpha (* $s $n)                   ; alpha = strength * count
       (let $beta (* (- 1 $s) $n)           ; beta = (1 - strength) * count
         (Beta $alpha $beta)))))

;(: beta-to-stv (-> Beta STV)) ; Type: Takes Beta expression, returns STV expression
(= (beta-to-stv (Beta $alpha $beta))
   (let $n (+ $alpha $beta)                  ; Total count
     (let $s (/ $alpha $n)                   ; Strength = alpha / (alpha + beta)
       (let $c (count-to-confidence $n)      ; Convert count to confidence
         (STV $s $c)))))

(= (adjust-stv $stvs)
 (let*
  (($betas (map-atom $stvs $stv (stv-to-beta $stv)))
   ($nbetas (adjust-beta-distributions $betas))
  )
  (map-atom $nbetas $beta (beta-to-stv $beta))
 )
)

(= (adjust-stv2 $stvs)
 (let*
  (($betas (map-atom $stvs $stv (stv-to-beta $stv)))
   ($nbetas (adjust-beta-distributions2 $betas))
  )
  (map-atom $nbetas $beta (beta-to-stv $beta))
 )
)

(= (ensure-tv-consistency $stvs)
 (let*
  (( ((STV $sa $ca) (STV $sb $cb) (STV $sab $cab)) $stvs)
   ($Lunbond (- (+ $sa $sb) 1))
   ($L (max-atom (0 $Lunbond)))
  )
 (if (<= (* $sa $sab) $sb)
   (adjust-stv $stvs)
   (if (<= $L (* $sa $sab))
     (adjust-stv2 $stvs)
     ($stva $stvb $stvab)
   )
)))

!(assertEqual (ensure-tv-consistency ((STV 0.5 0.1) (STV 0.1 0.1) (STV 0.9 0.1)))
 ((STV 0.1752577319587631 0.06310995445673391) (STV 0.17777777777777773 0.058823529411764726) (STV 0.872 0.07987220447284345)))
