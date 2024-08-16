
(: Nat Type)
(: Z Nat)
(: S (-> Nat Nat))

;; Define <=
(: <= (-> $a $a Bool))
(= (<= $x $y) (or (< $x $y) (== $x $y)))

;; Define cast functions between Nat and Number
(: fromNumber (-> Number Nat))
(= (fromNumber $n) (if (<= $n 0) Z (S (fromNumber (- $n 1)))))
(: fromNat (-> Nat Number))
(= (fromNat Z) 0)
(= (fromNat (S $k)) (+ 1 (fromNat $k)))



(: bc (-> $a                            ; Knowledge base space
          $b                            ; Query
          Nat                           ; Maximum depth
          $b))                          ; Result
;; Base case
(= (bc $kb (: $prf $ccln) $_) (match $kb (: $prf $ccln) (: $prf $ccln)))
;; Recursive step
(= (bc $kb (: ($prfabs $prfarg) $ccln) (S $k))
   (let* (((: $prfabs (-> $prms $ccln)) (bc $kb (: $prfabs (-> $prms $ccln)) $k))
          ((: $prfarg $prms) (bc $kb (: $prfarg $prms) $k)))
     (: ($prfabs $prfarg) $ccln)))

(: fc (-> $a                            ; Knowledge base space
          $b                            ; Source
          Nat                           ; Maximum depth
          $b))                          ; Conclusion
;; Base case
(= (fc $kb (: $prf $prms) $_) (: $prf $prms))
;; Recursive step
(= (fc $kb (: $prfarg $prms) (S $k))
   (let (: $prfabs (-> $prms $ccln)) (bc $kb (: $prfabs (-> $prms $ccln)) $k)
     (fc $kb (: ($prfabs $prfarg) $ccln) $k)))
(= (fc $kb (: $prfabs (-> $prms $ccln)) (S $k))
    (let (: $prfarg $prms) (bc $kb (: $prfarg $prms) $k)
     (fc $kb (: ($prfabs $prfarg) $ccln) $k)))


(= (clean $a)
    (case (trace! $a $a)
     (
      ((: $prf (-> $c $d)) (empty))
      ($_ $a)
     )
    )
)

(= (map $f $xs)
   (if (== $xs ()) ()
   (let* (($head (car-atom $xs))
          ($tail (cdr-atom $xs))
          ($mapped-head ($f $head))
          ($mapped-tail (map $f $tail)))
     ())))

(= (clean_fc $kb $query $n) (clean (fc $kb $query $n)))

(= (testd) (: p (-> a b)))
(= (testd) (: p c))
(= (testd) (: p b))

!(testd)
!(clean (testd))

