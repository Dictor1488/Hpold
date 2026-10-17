package inq.hpold.battle
{
   import flash.display.Bitmap;
   import flash.display.Sprite;
   import flash.text.TextField;
   import flash.text.TextFormat;
   import flash.filters.DropShadowFilter;

   public class HealthRow extends Sprite
   {
      [Embed(source="../../../../../../hpbars/hp_bg.png")]
      private static const BackgroundAsset:Class;
      [Embed(source="../../../../../../hpbars/hp_alive_l.png")]
      private static const AllyAsset:Class;
      [Embed(source="../../../../../../hpbars/hp_alive_r.png")]
      private static const EnemyAsset:Class;
      [Embed(source="../../../../../../hpbars/hp_alive_cb.png")]
      private static const ColorblindAsset:Class;

      public static const BAR_WIDTH:Number = 72;
      public static const TOTAL_WIDTH:Number = 88;
      public static const TOTAL_HEIGHT:Number = 18;
      private var _background:Bitmap;
      private var _fill:Bitmap;
      private var _text:TextField;
      private var _current:int = 0;
      private var _maximum:int = 0;
      private var _enemy:Boolean = false;
      private var _colorblind:Boolean = false;
      private var _showBar:Boolean = true;
      private var _renderedEnemy:Boolean = false;
      private var _renderedColorblind:Boolean = false;

      public function HealthRow()
      {
         super();
         mouseEnabled = false;
         mouseChildren = false;
         _background = new BackgroundAsset() as Bitmap;
         _fill = new AllyAsset() as Bitmap;
         _text = new TextField();
         _text.defaultTextFormat = new TextFormat("$FieldFont", 11, 0xFFFFFF, false, false, false, null, null, "center");
         _text.embedFonts = false;
         _text.selectable = false;
         _text.mouseEnabled = false;
         _text.width = 72;
         // OldSkool label anchor is 15px after the left bitmap and 16px
         // after the right bitmap (original x=100/85, -160/-176).
         _text.x = 15;
         _text.y = 3;
         _text.height = TOTAL_HEIGHT;
         _text.filters = [new DropShadowFilter(1, 90, 0x000000, 1, 2, 2, 2)];
         _background.x = 1;
         _background.y = 4;
         _fill.x = 0;
         _fill.y = 3;
         addChild(_background);
         addChild(_fill);
         addChild(_text);
         redraw();
      }

      public function get contentWidth():Number { return TOTAL_WIDTH; }

      public function setShowBar(value:Boolean):void
      {
         if (_showBar == value)
            return;
         _showBar = value;
         redraw();
      }

      public function setEnemyHpRed(value:Boolean):void
      {
         // Original skins use the original right-hand image, not class colors.
         redraw();
      }

      public function setColorblind(value:Boolean):void
      {
         if (_colorblind == value)
            return;
         _colorblind = value;
         redraw();
      }

      public function updateHealth(currentHealth:int, maxHealth:int, enemy:Boolean):void
      {
         var nextMaximum:int = Math.max(0, maxHealth);
         var nextCurrent:int = Math.min(nextMaximum, Math.max(0, currentHealth));
         if (_current == nextCurrent && _maximum == nextMaximum && _enemy == enemy)
            return;
         _current = nextCurrent;
         _maximum = nextMaximum;
         _enemy = enemy;
         redraw();
      }

      private function redraw():void
      {
         // OldSkool's original HTML draws the 72px image at a dynamically
         // calculated width. Do not crop via scrollRect: it shifts bitmap
         // coordinates and produces uneven HP fills.
         if (_renderedEnemy != _enemy || _renderedColorblind != _colorblind)
         {
            var asset:Bitmap;
            if (_enemy)
               asset = (_colorblind ? new ColorblindAsset() : new EnemyAsset()) as Bitmap;
            else
               asset = new AllyAsset() as Bitmap;
            _fill.bitmapData = asset.bitmapData;
            _renderedEnemy = _enemy;
            _renderedColorblind = _colorblind;
         }

         var ratio:Number = _maximum > 0
            ? Math.max(0, Math.min(1, Number(_current) / Number(_maximum)))
            : 0;
         // Mirrors math.ceil(72 * currentHP / maxHP) in OldSkool's Python.
         _fill.width = Math.ceil(BAR_WIDTH * ratio);
         _fill.height = 14;
         _fill.x = 0;
         _fill.y = 3;
         _background.visible = _showBar;
         _fill.visible = _showBar && _current > 0;
         _text.x = _enemy ? 16 : 15;
         _text.text = (_maximum > 0 && _current > 0)
            ? String(_current) + "/" + String(_maximum) : "";
      }
   }
}
