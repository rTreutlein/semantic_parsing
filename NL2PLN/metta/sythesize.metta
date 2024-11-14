;; Import modules

;;!(import! &self Num)
;;!(import! &self Intersection)

;; !(import! &self Unify.metta)

;; Enumerate all programs up to a given depth that are consistent with
;; the query, using the given axiom non-deterministic functions and rules.
;;
;; The arguments are:
;;
;; $query: an Atom under the form (: TERM TYPE).  The atom may contain
;;         free variables within TERM and TYPE to form various sort of
;;         queries, such as:
;;         1. Backward chaining: (: $term (Inheritance $x Mammal))
;;         2. Forward chaining: (: ($rule $premise AXIOM) $type)
;;         3. Mixed chaining: (: ($rule $premise AXIOM) (Inheritance $x Mammal))
;;         4. Type checking: (: TERM TYPE)
;;         5. Type inference: (: TERM $type)
;;
;; $kb: a nullary function to axiom, to non-deterministically pick up
;;      an axiom.  An axiom is an Atom of the form (: TERM TYPE).
;;
;; $rb: a nullary function to rule, to non-deterministically pick up a
;;      rule.  A rule is a function mapping premises to conclusion,
;;      where premises and conclusion have the form (: TERM TYPE).
;;
;; $depth: a Nat representing the maximum depth of the generated
;;         programs.
;;
;; TODO: recurse over curried rules instead of duplicating code over
;; tuples.
(: synthesize (-> $a (-> $kt) (-> $s $rt) $s Nat $a))
;; Nullary rule (axiom)
(= (synthesize $query $kb $rb Z $depth)
   (let $query ($kb) $query))
;; Unary rule
(= (synthesize $query $kb $rb $s (S $k))
   (let* (((: $ructor (-> $premise $conclusion)) ($rb $s))
          ((: ($ructor $proof) $conclusion) $query)
          ((: $proof $premise) (synthesize (: $proof $premise) $kb $rb Z $k)))
     $query))
;; Binary rule
(= (synthesize $query $kb $rb $s (S $k))
   (let* (((: $ructor (-> $premise1 $premise2 $conclusion)) ($rb $s))
          ((: ($ructor $proof1 $proof2) $conclusion) $query)
          ((: $proof1 $premise1) (synthesize (: $proof1 $premise1) $kb $rb Z $k))
          ((: $proof2 $premise2) (synthesize (: $proof2 $premise2) $kb $rb Z $k)))
     $query))

;; Define ad-atom-nodup, that adds an atom only if it is not already
;; in the atomspace
(: add-atom-nodup (-> $st Atom Atom ()))
(= (add-atom-nodup $kb $atom $a2)
   (case (let $atom ($kb) $atom)
     (($atom Empty)
      ($_ (add-atom &self $a2)))))


(= (fc $kb $rb)
    (let* (($out (synthesize (: $term $type) $kb $rb S (S Z)))
           ($dummy (add-atom-nodup $kb $out (= ($kb) $out)))
          )
    $out
))
