;; Define Nat
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

;;;;;;;;;;;;;;;;;;;;;;
;; Backward chainer ;;
;;;;;;;;;;;;;;;;;;;;;;
(: bc (-> $a                            ; Knowledge base space
          Nat                           ; Maximum depth
          $q                            ; Query
          $r))                          ; Result

;; Base case
(= (bc $kb $_ (: $prf $thrm))
   (match $kb (: $prf $thrm) (: $prf $thrm)))

; Recursive step
(= (bc $kb (S $k) (: ($prfabs $prfarg) $thrm))
   (let* (((: $prfabs (-> (: $prfarg $prms) $thrm))
           (bc $kb $k (: $prfabs (-> (: $prfarg $prms) $thrm))))
          ((: $prfarg $prms)
           (bc $kb $k (: $prfarg $prms))))
     (unify $kb (: ($prfabs $prfarg) $thrm) (Empty) (: ($prfabs $prfarg) $thrm))))

;;;;;;;;;;;;;;;;;;;;;
;; Forward chainer ;;
;;;;;;;;;;;;;;;;;;;;;

(: fc (-> $a                            ; Knowledge base space
          Nat                           ; Maximum depth
          $q                            ; Query
          $r))                          ; Result

;;Base case
(= (fc $kb $_ (: $prf $thrm)) (: $prf $thrm))

;;Recursive step
(= (fc $kb (S $k) (: $prfarg $prms))
    (let (: $prfabs (-> (: $prfarg $prms) $ccln)) 
         (bc $kb $k (: $prfabs (-> (: $prfarg $prms) $ccln)))
         (fc $kb $k (: ($prfabs $prfarg) $ccln))))

(= (fc $kb (S $k) (: $prfabs (-> (: $prfarg $prms) $ccln)))
   (let (: $prfarg $prms) 
        (bc $kb $k (: $prfarg $prms)))
        (fc $kb $k (: ($prfabs $prfarg) $ccln)))

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


;; Define ad-atom-nodup, that adds an atom only if it is not already
;; in the atomspace
(: add-atom-nodup (-> $st Atom ()))
(= (add-atom-nodup $space $atom)
   (case (match $space $atom $atom)
     (($atom (Empty))
      (Empty (add-atom $space $atom)))))

(: add-atom-nodup (-> $st Atom ()))
(= (add-atom-nodup-nofail $space $atom)
   (case (match $space $atom $atom)
     (($atom ())
      (Empty (add-atom $space $atom)))))

(= (ddfc $kb $query)
    (let* (($out (fc $kb (S (S Z)) $query))
           ($dummy (add-atom-nodup $kb $out))
          )
    $out
))

;;deduplicatig bc
(= (ddbc $kb $query)
    (let* (($out (bc $kb (S (S Z)) $query))
           ($dummy (add-atom-nodup-nofail $kb $out))
          )
    $out
))
